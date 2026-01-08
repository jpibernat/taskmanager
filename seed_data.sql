-- Areas
INSERT INTO dbo.Areas (AreaName) VALUES
('IT'), ('Finance'), ('HR'), ('Operations');
GO

-- Priorities
INSERT INTO dbo.Priorities (PriorityName) VALUES
('Low'), ('Medium'), ('High'), ('Critical');
GO

-- Topic Types
INSERT INTO dbo.TopicTypes (TypeName) VALUES
('Incident'), ('Request'), ('Project'), ('Task');
GO

-- Statuses
INSERT INTO dbo.Statuses (StatusName) VALUES
('Open'), ('In Progress'), ('On Hold'), ('Resolved'), ('Closed');
GO

-- Users
INSERT INTO dbo.Users (UserName, Email, Role) VALUES
('Alice Johnson', 'alice@example.com', 'Manager'),
('Bob Smith', 'bob@example.com', 'Analyst'),
('Carol White', 'carol@example.com', 'Technician'),
('David Brown', 'david@example.com', 'Developer');
GO

-- Example Topic
INSERT INTO dbo.Topics (Title, Description, AreaID, PriorityID, TypeID, StatusID, StartDate, DueDate, Timeframe, CreatedBy, AssignedTo)
VALUES (
    'Server outage in datacenter',
    'Critical incident affecting production servers',
    1, -- IT
    4, -- Critical
    1, -- Incident
    1, -- Open
    '2025-12-22',
    '2025-12-23',
    '24h',
    1, -- Alice
    3  -- Carol
);
GO

-- Example Update
INSERT INTO dbo.TopicUpdates (TopicID, Comment, UpdatedBy)
VALUES (1, 'Investigating root cause of outage', 3);
GO

-- Example Status History
INSERT INTO dbo.TopicStatusHistory (TopicID, OldStatusID, NewStatusID, ChangedBy, Comment)
VALUES (1, 1, 2, 3, 'Started working on resolution');
GO
