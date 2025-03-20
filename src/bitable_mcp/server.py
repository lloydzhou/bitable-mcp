import os, json
from mcp.server.fastmcp import FastMCP
from pybitable import Connection, ConnectionPool
from pybitable.dbapi import logger

# logger.setLevel("DEBUG")

mcp = FastMCP(
    name="bitable",
    instructions="This MCP server provides access to Lark bitable through the Model Context Protocol."
)

def connection_factory():
    personal_base_token = os.environ['PERSONAL_BASE_TOKEN']
    app_token = os.environ['APP_TOKEN']
    db_url = f'bitable+pybitable://:{personal_base_token}@base-api.feishu.cn/{app_token}'
    return Connection(db_url)

conn_pool = ConnectionPool(
    maxsize=10,
    connection_factory=connection_factory,
)

@mcp.tool(
    name="list_table",
    description="list table for current bitable",
)
def list_table() -> list[str]:
    with conn_pool.connect() as connection:
        logger.error("connection %r", connection)
        logger.error("bot %r", connection.bot)
        logger.error("bot %r", connection.bot.personal_base_token)
        cursor = connection.cursor()
        tables = cursor.execute('show tables').fetchall()
        return json.dumps(tables)

@mcp.tool(
    name="describe_table",
    description="describe_table by table name",
)
def describe_table(name: str) -> list[str]:
    with conn_pool.connect() as connection:
        cursor = connection.cursor()
        columns, _ = cursor.get_columns({
            "select": {
                "all_columns": True
            },
            "from": name,
        })
        return json.dumps(columns)


@mcp.tool(
    name="read_query",
    description="read_query by sql",
)
def read_query(sql: str) -> list[str]:
    with conn_pool.connect() as connection:
        cursor = connection.cursor()
        result = cursor.execute(sql).fetchall()
        return json.dumps(result)

if __name__ == "__main__":    
    mcp.run()
