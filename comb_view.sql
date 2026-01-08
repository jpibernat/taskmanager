IF OBJECT_ID('dbo.vw_ManagementSnapshot', 'V') IS NOT NULL DROP VIEW dbo.vw_ManagementSnapshot;
GO

CREATE VIEW dbo.vw_ManagementSnapshot AS
SELECT 
    -- Status overview
    (SELECT STRING_AGG(CONCAT(StatusName, ': ', TopicCount), '; ')
     FROM (
         SELECT s.StatusName, COUNT(*) AS TopicCount
         FROM dbo.Topics t
         JOIN dbo.Statuses s ON t.StatusID = s.StatusID
         GROUP BY s.StatusName
     ) AS StatusCounts) AS StatusSummary,

    -- Priority overview
    (SELECT STRING_AGG(CONCAT(PriorityName, ': ', TopicCount), '; ')
     FROM (
         SELECT p.PriorityName, COUNT(*) AS TopicCount
         FROM dbo.Topics t
         JOIN dbo.Priorities p ON t.PriorityID = p.PriorityID
         GROUP BY p.PriorityName
     ) AS PriorityCounts) AS PrioritySummary,

    -- Overdue vs On-Time
    (SELECT STRING_AGG(CONCAT(DeadlineStatus, ': ', TopicCount), '; ')
     FROM (
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
             END
     ) AS DeadlineCounts) AS DeadlineSummary,

    -- Workload distribution
    (SELECT STRING_AGG(CONCAT(UserName, ': ', AssignedCount), '; ')
     FROM (
         SELECT u.UserName, COUNT(*) AS AssignedCount
         FROM dbo.Topics t
         JOIN dbo.Users u ON t.AssignedTo = u.UserID
         GROUP BY u.UserName
     ) AS WorkloadCounts) AS WorkloadSummary;
GO
