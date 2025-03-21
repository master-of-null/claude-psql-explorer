import os
import sys
from langchain_anthropic import ChatAnthropic
from langchain_community.utilities import SQLDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URI from environment variables
db_uri = os.getenv("DB_URI")
db_schema = os.getenv("DB_SCHEMA") or "catalog"
if not db_uri:
    raise ValueError("DB_URI not found in environment variables. Please set it in your .env file.")

# Initialize database with specific schema
db = SQLDatabase.from_uri(
    db_uri,
    schema=db_schema,
    include_tables=None,  # Include all tables in the schema
    sample_rows_in_table_info=3  # Include sample rows for better context
)

# Set up Claude model with the latest version
llm = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    max_tokens=4000  # Set higher token limit for responses
)

# Get the database schema information
def get_detailed_schema_info():
    """Get detailed schema information including tables, columns, and relationships"""
    base_info = db.get_table_info()
    
    # Get additional information about foreign keys and constraints
    try:
        fk_query = f"""
        SELECT
            tc.table_schema, 
            tc.constraint_name, 
            tc.table_name, 
            kcu.column_name, 
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name 
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = '{db_schema}';
        """
        
        fk_info = db.run(fk_query)
        return base_info + "\n\nForeign key relationships:\n" + fk_info
    except Exception as e:
        print(f"Warning: Could not fetch foreign key relationships: {e}")
        # If the foreign key query fails, just return the base schema info
        return base_info

# Get detailed schema information
schema_info = get_detailed_schema_info()

def answer_question(question):
    """Answer a direct question about the database"""
    prompt = f"""You are a PostgreSQL database expert. Answer the following question based on the database schema information provided.

Database schema information:
{schema_info}

Question: {question}

If the question requires a SQL query to answer, provide the query.
If you need to reference tables in your query, always include the schema name '{db_schema}'.
Be specific, accurate, and provide exactly what was asked for.
"""
    
    response = llm.invoke(prompt).content.strip()
    print("\n----- Answer -----")
    print(response)
    print("-----------------\n")
    return response

def analyze_database_model(question):
    """Use Claude to analyze the database model based on the schema information"""
    prompt = f"""You are a database design expert specializing in analyzing data models and database schemas.
    
I'm going to provide you with schema information from a PostgreSQL database, and I'd like you to analyze its design, structure, and relationships.

Database schema information:
{schema_info}

My question or request is: {question}

Please analyze this database schema and provide insights on:
1. The overall purpose and domain of this database
2. The key entities and their relationships
3. The database design patterns being used
4. Any normalization or denormalization approaches
5. Potential strengths and weaknesses in the design
6. Any specific aspects I've asked about in my question

Format your response in a clear, organized way with headings and bullet points where appropriate.
If you identify any entity-relationship diagrams that would be helpful, describe them in text form.
"""
    
    response = llm.invoke(prompt).content.strip()
    print("\n----- Database Model Analysis -----")
    print(response)
    print("-----------------------------------\n")
    return response

def generate_sql_query(question):
    """Generate a SQL query to answer a specific data question"""
    prompt = f"""You are a PostgreSQL expert. Generate a SQL query to answer the user's question.

Database schema information:
{schema_info}

Only use the tables and columns mentioned in the schema.
Always reference tables with the schema name "{db_schema}" (e.g., {db_schema}.table_name).
Return the SQL query first, followed by an explanation of what the query does.

User question: {question}
"""
    
    response = llm.invoke(prompt).content.strip()
    
    # Attempt to extract just the SQL query from the response
    lines = response.split('\n')
    query_lines = []
    in_query = False
    
    for line in lines:
        if line.strip().startswith('```') and not in_query:
            in_query = True
            continue
        elif line.strip().startswith('```') and in_query:
            in_query = False
            break
        elif in_query:
            query_lines.append(line)
    
    # If we successfully extracted a query between code blocks
    if query_lines:
        sql_query = '\n'.join(query_lines).strip()
    else:
        # Fallback to getting the first few lines which are likely the query
        sql_query = '\n'.join(lines[:5]).strip()
    
    print(f"\nGenerated SQL: {sql_query}\n")
    
    try:
        result = db.run(sql_query)
        print(f"Result: {result}")
        print("\nFull explanation:")
        print(response)
        return result
    except Exception as e:
        print(f"Error executing SQL: {e}")
        print("\nFull response:")
        print(response)
        return f"Error: {e}"

def explore_db():
    """Browse and explore tables in the database"""
    # Print database schema information
    tables = db.get_usable_table_names()
    print(f"Available tables in '{db_schema}' schema: {', '.join(tables)}")
    
    selected_table = input("\nWhich table would you like to examine? ")
    if selected_table in tables:
        sample_query = f"SELECT * FROM {db_schema}.{selected_table} LIMIT 5;"
        print(f"\nExecuting: {sample_query}")
        result = db.run(sample_query)
        print(f"Sample data: {result}")
    else:
        print(f"Table not found in the {db_schema} schema.")

def read_markdown_question(filepath="./question.md"):
    """Read a question from a markdown file"""
    try:
        with open(filepath, 'r') as file:
            content = file.read()
            return content.strip()
    except FileNotFoundError:
        raise ValueError(f"Error: File {filepath} not found.")
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def process_markdown_mode():
    """Process a question from a markdown file"""
    question = read_markdown_question()
    if question:
        print(f"\nProcessing question from question.md:\n{question}\n")
        
        # Check for explicit prefixes
        if question.lower().startswith('query:'):
            query = question[6:].strip()
            generate_sql_query(query)
        elif question.lower().startswith('model:'):
            model_q = question[6:].strip()
            analyze_database_model(model_q)
        else:
            # Just answer the question directly
            answer_question(question)
    else:
        print("No question found in question.md file.")

# Main execution
if __name__ == "__main__":
    # Check if required environment variables are set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not found in environment variables.")
        print("Add to your .env file or set it manually.")
        sys.exit(1)
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--file":
        # File mode - read from question.md
        process_markdown_mode()
    else:
        # Interactive mode
        print(f"Database Analyzer - {db_schema} schema")
        print("---------------------------------------")
        print("Commands:")
        print("  'explore' - Browse tables and see sample data")
        print("  'query: [your question]' - Generate and run a SQL query")
        print("  'model: [your question]' - Analyze database model/design")
        print("  'exit' - Quit the application")
        print("  'file' - Read question from question.md file")
        print("  Any other input - Ask a question about the database")
        print("---------------------------------------")
        
        while True:
            user_input = input("\nEnter your question or command: ")
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'explore':
                explore_db()
            elif user_input.lower() == 'file':
                process_markdown_mode()
            elif user_input.lower().startswith('query:'):
                query = user_input[6:].strip()
                generate_sql_query(query)
            elif user_input.lower().startswith('model:'):
                model_q = user_input[6:].strip()
                analyze_database_model(model_q)
            else:
                # Just answer the question directly
                answer_question(user_input)