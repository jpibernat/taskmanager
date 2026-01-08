-- Drop existing tables if they exist (clean slate)
IF OBJECT_ID('dbo.TopicStatusHistory', 'U') IS NOT NULL DROP TABLE dbo.TopicStatusHistory;
IF OBJECT_ID('dbo.TopicUpdates', 'U') IS NOT NULL DROP TABLE dbo.TopicUpdates;
IF OBJECT_ID('dbo.Topics', 'U') IS NOT NULL DROP TABLE dbo.Topics;
IF OBJECT_ID('dbo.Statuses', 'U') IS NOT NULL DROP TABLE dbo.Statuses;
IF OBJECT_ID('dbo.TopicTypes', 'U') IS NOT NULL DROP TABLE dbo.TopicTypes;
IF OBJECT_ID('dbo.Priorities', 'U') IS NOT NULL DROP TABLE dbo.Priorities;
IF OBJECT_ID('dbo.Areas', 'U') IS NOT NULL DROP TABLE dbo.Areas;
IF OBJECT_ID('dbo.Users', 'U') IS NOT NULL DROP TABLE dbo.Users;
GO

-- Users
CREATE TABLE dbo.Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    UserName VARCHAR(100) NOT NULL,
    Email VARCHAR(150),
    Role VARCHAR(50)
);
GO

-- Areas
CREATE TABLE dbo.Areas (
    AreaID INT IDENTITY(1,1) PRIMARY KEY,
    AreaName VARCHAR(100) NOT NULL
);
GO

-- Priorities
CREATE TABLE dbo.Priorities (
    PriorityID INT IDENTITY(1,1) PRIMARY KEY,
    PriorityName VARCHAR(50) NOT NULL
);
GO

-- Topic Types
CREATE TABLE dbo.TopicTypes (
    TypeID INT IDENTITY(1,1) PRIMARY KEY,
    TypeName VARCHAR(50) NOT NULL
);
GO

-- Statuses
CREATE TABLE dbo.Statuses (
    StatusID INT IDENTITY(1,1) PRIMARY KEY,
    StatusName VARCHAR(50) NOT NULL
);
GO

-- Topics
CREATE TABLE dbo.Topics (
    TopicID INT IDENTITY(1,1) PRIMARY KEY,
    Title VARCHAR(200) NOT NULL,
    Description NVARCHAR(MAX),
    AreaID INT FOREIGN KEY REFERENCES dbo.Areas(AreaID),
    PriorityID INT FOREIGN KEY REFERENCES dbo.Priorities(PriorityID),
    TypeID INT FOREIGN KEY REFERENCES dbo.TopicTypes(TypeID),
    StatusID INT FOREIGN KEY REFERENCES dbo.Statuses(StatusID),
    StartDate DATE,
    DueDate DATE,
    Timeframe VARCHAR(50),
    CreatedBy INT FOREIGN KEY REFERENCES dbo.Users(UserID),
    AssignedTo INT FOREIGN KEY REFERENCES dbo.Users(UserID)
);
GO

-- Topic Updates (comments & progress notes)
CREATE TABLE dbo.TopicUpdates (
    UpdateID INT IDENTITY(1,1) PRIMARY KEY,
    TopicID INT NOT NULL FOREIGN KEY REFERENCES dbo.Topics(TopicID),
    UpdateDate DATETIME2 DEFAULT SYSUTCDATETIME(),
    Comment NVARCHAR(MAX),
    UpdatedBy INT FOREIGN KEY REFERENCES dbo.Users(UserID)
);
GO

-- Topic Status History (workflow transitions)
CREATE TABLE dbo.TopicStatusHistory (
    HistoryID INT IDENTITY(1,1) PRIMARY KEY,
    TopicID INT NOT NULL FOREIGN KEY REFERENCES dbo.Topics(TopicID),
    OldStatusID INT FOREIGN KEY REFERENCES dbo.Statuses(StatusID),
    NewStatusID INT FOREIGN KEY REFERENCES dbo.Statuses(StatusID),
    ChangedBy INT FOREIGN KEY REFERENCES dbo.Users(UserID),
    ChangeDate DATETIME2 DEFAULT SYSUTCDATETIME(),
    Comment NVARCHAR(MAX)
);
GO
