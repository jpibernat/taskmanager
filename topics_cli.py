import pyodbc

# Connection setup
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=LARRCBDZ6RGY3\SQLEXPRESS;"          # replace with your server
    "DATABASE=Topics;" # replace with your DB
    "UID=dbo;"
    "PWD=Marc0s.2o2%+;"
)
cursor = conn.cursor()

# --- Insert Functions ---
def add_user():
    name = input("Enter user name: ")
    email = input("Enter email: ")
    role = input("Enter role: ")
    cursor.execute("INSERT INTO dbo.Users (UserName, Email, Role) VALUES (?, ?, ?)", (name, email, role))
    conn.commit()
    print("✅ User added.")

def add_topic():
    title = input("Enter topic title: ")
    description = input("Enter description: ")
    area_id = int(input("Enter AreaID: "))
    priority_id = int(input("Enter PriorityID: "))
    type_id = int(input("Enter TypeID: "))
    status_id = int(input("Enter StatusID: "))
    start_date = input("Enter start date (YYYY-MM-DD): ")
    due_date = input("Enter due date (YYYY-MM-DD): ")
    timeframe = input("Enter timeframe: ")
    created_by = int(input("Enter CreatedBy UserID: "))
    assigned_to = int(input("Enter AssignedTo UserID: "))
    cursor.execute("""
        INSERT INTO dbo.Topics 
        (Title, Description, AreaID, PriorityID, TypeID, StatusID, StartDate, DueDate, Timeframe, CreatedBy, AssignedTo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, description, area_id, priority_id, type_id, status_id,
          start_date, due_date, timeframe, created_by, assigned_to))
    conn.commit()
    print("✅ Topic added.")

def add_update():
    topic_id = int(input("Enter TopicID: "))
    comment = input("Enter update comment: ")
    updated_by = int(input("Enter UpdatedBy UserID: "))
    cursor.execute("INSERT INTO dbo.TopicUpdates (TopicID, Comment, UpdatedBy) VALUES (?, ?, ?)", (topic_id, comment, updated_by))
    conn.commit()
    print("✅ Update added.")

def change_status():
    topic_id = int(input("Enter TopicID: "))
    old_status_id = int(input("Enter OldStatusID: "))
    new_status_id = int(input("Enter NewStatusID: "))
    changed_by = int(input("Enter ChangedBy UserID: "))
    comment = input("Enter status change comment: ")
    cursor.execute("""
        INSERT INTO dbo.TopicStatusHistory (TopicID, OldStatusID, NewStatusID, ChangedBy, Comment)
        VALUES (?, ?, ?, ?, ?)
    """, (topic_id, old_status_id, new_status_id, changed_by, comment))
    conn.commit()
    print("✅ Status change recorded.")

# --- View Functions ---
def list_topics():
    cursor.execute("SELECT TopicID, Title, DueDate FROM dbo.Topics")
    for row in cursor.fetchall():
        print(f"ID: {row.TopicID}, Title: {row.Title}, Due: {row.DueDate}")

def show_updates():
    topic_id = int(input("Enter TopicID: "))
    cursor.execute("""
        SELECT tu.UpdateDate, tu.Comment, u.UserName
        FROM dbo.TopicUpdates tu
        JOIN dbo.Users u ON tu.UpdatedBy = u.UserID
        WHERE tu.TopicID = ?
        ORDER BY tu.UpdateDate ASC
    """, (topic_id,))
    for row in cursor.fetchall():
        print(f"{row.UpdateDate} - {row.UserName}: {row.Comment}")

def show_status_history():
    topic_id = int(input("Enter TopicID: "))
    cursor.execute("""
        SELECT h.ChangeDate, s1.StatusName AS OldStatus, s2.StatusName AS NewStatus, u.UserName, h.Comment
        FROM dbo.TopicStatusHistory h
        JOIN dbo.Statuses s1 ON h.OldStatusID = s1.StatusID
        JOIN dbo.Statuses s2 ON h.NewStatusID = s2.StatusID
        JOIN dbo.Users u ON h.ChangedBy = u.UserID
        WHERE h.TopicID = ?
        ORDER BY h.ChangeDate ASC
    """, (topic_id,))
    for row in cursor.fetchall():
        print(f"{row.ChangeDate}: {row.OldStatus} → {row.NewStatus} by {row.UserName} ({row.Comment})")

# --- Menu Loop ---
def menu():
    while True:
        print("\n--- Management CLI ---")
        print("1. Add User")
        print("2. Add Topic")
        print("3. Add Update")
        print("4. Change Status")
        print("5. List Topics")
        print("6. Show Updates for Topic")
        print("7. Show Status History for Topic")
        print("8. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            add_user()
        elif choice == "2":
            add_topic()
        elif choice == "3":
            add_update()
        elif choice == "4":
            change_status()
        elif choice == "5":
            list_topics()
        elif choice == "6":
            show_updates()
        elif choice == "7":
            show_status_history()
        elif choice == "8":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    menu()
