IF OBJECT_ID('dbo.vw_TopicsByStatus', 'V') IS NOT NULL DROP VIEW dbo.vw_TopicsByStatus;
GO
CREATE VIEW dbo.vw_TopicsByStatus AS
SELECT s.StatusName, COUNT(*) AS TopicCount
FROM dbo.Topics t
JOIN dbo.Statuses s ON t.StatusID = s.StatusID
GROUP BY s.StatusName;
GO

IF OBJECT_ID('dbo.vw_TopicsByPriority', 'V') IS NOT NULL DROP VIEW dbo.vw_TopicsByPriority;
GO
CREATE VIEW dbo.vw_TopicsByPriority AS
SELECT p.PriorityName, COUNT(*) AS TopicCount
FROM dbo.Topics t
JOIN dbo.Priorities p ON t.PriorityID = p.PriorityID
GROUP BY p.PriorityName;
GO

IF OBJECT_ID('dbo.vw_TopicsDeadlineStatus', 'V') IS NOT NULL DROP VIEW dbo.vw_TopicsDeadlineStatus;
GO
CREATE VIEW dbo.vw_TopicsDeadlineStatus AS
SELECT 
    CASE 
        WHEN t.DueDate < CAST(GETDATE() AS DATE) AND s.StatusName <> 'Closed' THEN 'Overdue'
        ELSE 'On Time'
    END AS DeadlineStatus,
    COUNT(*) AS TopicCount
FROM dbo.Topics t
JOIN dbo.Statuses s ON t.StatusID = s.StatusID
GROUP BY 
    CASE 
        WHEN t.DueDate < CAST(GETDATE() AS DATE) AND s.StatusName <> 'Closed' THEN 'Overdue'
        ELSE 'On Time'
    END;
GO

IF OBJECT_ID('dbo.vw_TopicsByUser', 'V') IS NOT NULL DROP VIEW dbo.vw_TopicsByUser;
GO
CREATE VIEW dbo.vw_TopicsByUser AS
SELECT u.UserName, COUNT(*) AS AssignedCount
FROM dbo.Topics t
JOIN dbo.Users u ON t.AssignedTo = u.UserID
GROUP BY u.UserName;
GO

IF OBJECT_ID('dbo.vw_TopicsByTypeStatus', 'V') IS NOT NULL DROP VIEW dbo.vw_TopicsByTypeStatus;
GO
CREATE VIEW dbo.vw_TopicsByTypeStatus AS
SELECT tt.TypeName, s.StatusName, COUNT(*) AS TopicCount
FROM dbo.Topics t
JOIN dbo.TopicTypes tt ON t.TypeID = tt.TypeID
JOIN dbo.Statuses s ON t.StatusID = s.StatusID
GROUP BY tt.TypeName, s.StatusName;
GO

IF OBJECT_ID('dbo.vw_UpcomingDeadlines', 'V') IS NOT NULL DROP VIEW dbo.vw_UpcomingDeadlines;
GO
CREATE VIEW dbo.vw_UpcomingDeadlines AS
SELECT t.TopicID, t.Title, t.DueDate, u.UserName AS AssignedTo, s.StatusName
FROM dbo.Topics t
JOIN dbo.Users u ON t.AssignedTo = u.UserID
JOIN dbo.Statuses s ON t.StatusID = s.StatusID
WHERE t.DueDate BETWEEN CAST(GETDATE() AS DATE) AND DATEADD(DAY, 7, CAST(GETDATE() AS DATE));
GO
