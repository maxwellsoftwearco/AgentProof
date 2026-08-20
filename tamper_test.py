import sqlite3


connection = sqlite3.connect("agentproof.db")

cursor = connection.cursor()

cursor.execute(
    """
    UPDATE receipts
    SET action = ?
    WHERE receipt_id = ?
    """,
    (
        "DELETE_DATABASE",
        "AP-6326AC3C08BE4046",
    ),
)

connection.commit()
connection.close()

print("Database modified.")