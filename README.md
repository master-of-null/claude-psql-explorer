# Database Model Analyzer

A tool that uses Claude AI to analyze and explain PostgreSQL database schemas, helping you understand database design, relationships, and architecture. You can interact with it to explore your database structure and optionally generate SQL queries.

## Features

- **Database Design Analysis**: Understand how your database is structured, including relationships, patterns, and design decisions
- **Schema Exploration**: View available tables and sample data
- **Query Generation**: Optionally generate SQL queries for data questions
- **Multiple Usage Modes**: Use interactively or with prepared questions in a markdown file

## Prerequisites

- Python 3.11+
- PostgreSQL database
- Anthropic API key (Claude)

## Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On macOS/Linux
   source venv/bin/activate
   
   # On Windows
   venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the provided `.env.example`:
   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file with your API key and database connection details:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   DB_URI=postgresql://username:password@host:port/database_name
   DB_SCHEMA=public
   ```

## Usage

### Interactive Mode

Run the application in interactive mode:
```bash
python app.py
```

Available commands:
- Ask any question about the database model (default behavior)
- `query: [your question]` - Generate and run a SQL query
- `explore` - Browse tables and see sample data
- `file` - Process a question from question.md file
- `exit` - Quit the application

### File Mode

You can provide your question in a markdown file (question.md) and run:
```bash
python app.py --file
```

This will process the contents of `question.md` and display the analysis.

## Example Questions

### Database Model Analysis
- "What is the overall structure of this database?"
- "Explain the relationships between the main entities"
- "What design patterns are being used in this schema?"
- "How is the data normalized in this model?"
- "Identify potential performance issues in this schema design"

### SQL Queries
- "query: How many records are in each table?"
- "query: What are the top 5 largest tables by row count?"
- "query: Show the relationships between the main tables"

## How It Works

1. The tool connects to your PostgreSQL database and extracts schema information
2. It gathers detailed metadata about tables, columns, and relationships
3. When you ask a question, it passes the schema information and your question to Claude
4. Claude analyzes the schema and provides insights into the database design
5. For query requests, it generates PostgreSQL-compatible SQL to answer your question

## Troubleshooting

### Database Connection Issues
- Make sure your PostgreSQL server is running
- Verify the connection details in your `.env` file
- If using a remote database, check firewall settings

## Customization

- Edit the prompts in the `analyze_database_model` and `generate_sql_query` functions to adjust the analysis style
- Modify the `get_detailed_schema_info` function to gather additional database metadata
- Add support for additional database schemas by updating the SQLDatabase initialization

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
