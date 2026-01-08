-- Topics by Status
CREATE VIEW vw_TopicsByStatus AS
SELECT s.StatusName, COUNT(*) AS TopicCount
FROM Topics t
JOIN Statuses s ON t.StatusID = s.StatusID
GROUP BY s.StatusName;

-- Topics by Priority
CREATE VIEW vw_TopicsByPriority AS
SELECT p.PriorityName, COUNT(*) AS TopicCount
FROM Topics t
JOIN Priorities p ON t.PriorityID = p.PriorityID
GROUP BY p.PriorityName;

-- Overdue vs On-Time
CREATE VIEW vw_TopicsDeadlineStatus AS
SELECT 
    CASE 
        WHEN t.DueDate < CAST(GETDATE() AS DATE) AND s.StatusName <> 'Closed' THEN 'Overdue'
        ELSE 'On Time'
    END AS DeadlineStatus,
    COUNT(*) AS TopicCount
FROM Topics t
JOIN Statuses s ON t.StatusID = s.StatusID
GROUP BY 
    CASE 
        WHEN t.DueDate < CAST(GETDATE() AS DATE) AND s.StatusName <> 'Closed' THEN 'Overdue'
        ELSE 'On Time'
    END;

-- Workload per User
CREATE VIEW vw_TopicsByUser AS
SELECT u.UserName, COUNT(*) AS AssignedCount
FROM Topics t
JOIN Users u ON t.AssignedTo = u.UserID
GROUP BY u.UserName;

-- Topics by Type and Status
CREATE VIEW vw_TopicsByTypeStatus AS
SELECT tt.TypeName, s.StatusName, COUNT(*) AS TopicCount
FROM Topics t
JOIN TopicTypes tt ON t.TypeID = tt.TypeID
JOIN Statuses s ON t.StatusID = s.StatusID
GROUP BY tt.TypeName, s.StatusName;

-- Upcoming Deadlines (Next 7 Days)
CREATE VIEW vw_UpcomingDeadlines AS
SELECT t.TopicID, t.Title, t.DueDate, u.UserName AS AssignedTo, s.StatusName
FROM Topics t
JOIN Users u ON t.AssignedTo = u.UserID
JOIN Statuses s ON t.StatusID = s.StatusID
WHERE t.DueDate BETWEEN CAST(GETDATE() AS DATE) AND DATEADD(DAY, 7, CAST(GETDATE() AS DATE))
ORDER BY t.DueDate ASC;
