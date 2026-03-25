# Architecture

C4 model structure of the search engine project:

## 1. System Context
The system is a local search engine which enables the user to search files from their computer by:
- file name
- file content
- file metadata
The search engine scans files, stores useful data in a database, and returns matching results to the user.

### Main actor
- **User** – searches for files and views the results.

### External element
- **Local file system** – the place from which files are read.

### Indexing flow
1. The crawler finds files.
2. The reader reads text content.
3. The metadata extractor collects metadata.
4. The indexer stores everything in the database.

### Search flow
1. The user types a query.
2. The query processor searches the database.
3. The preview generator prepares short snippets.
4. The interface shows the results.

## 2. Containers

### 2.1 User Interface
- receiving the user query
- showing the search results
- showing a short preview of each matching file

### 2.2 Search Engine Application
- reading files
- scanning folders
- extracting content and metadata
- sending data to the database
- searching the indexed data

### 2.3 Database
Responsible for storing:
- file path
- file name
- file content
- metadata
- preview text

## 3. Components

### 3.1 User Interface

```text
+----------------------+
|     User Interface   |
+----------------------+
| Search Input Module  |
| Results Module       |
| Filter Tags          |
| Preview Panel        |
+----------------------+
```

- **Search Input Module** – receives the query from the user
- **Results Module** – updates and shows matched files in the same window while the user types
- **Filter Tags** – lets the user refine results quickly
- **Preview Panel** – shows a short text preview for the selected result

### 3.2 Search Engine Application

```text
+-----------------------------------+
|     Search Engine Application     |
+-----------------------------------+
| File Crawler                      |
| File Reader                       |
| Metadata Extractor                |
| Indexer                           |
| Query Processor                   |
| Preview Generator                 |
+-----------------------------------+
```

- **File Crawler** – walks through folders
- **File Reader** – reads text from files
- **Metadata Extractor** – gets file information
- **Indexer** – saves data into the database
- **Query Processor** – handles search queries
- **Preview Generator** – builds short snippets

### 3.3 Database

```text
+----------------------+
|       Database       |
+----------------------+
| Files Table          |
| Metadata Table       |
| Search Index         |
+----------------------+
```

- **Files Table** – stores file path, name, and content
- **Metadata Table** – stores metadata like size and timestamps
- **Search Index** – helps fast searching in text

## 4. Classes


```text
File Crawler
 ├─ FileCrawler
 └─ FileScanner

File Reader
 ├─ FileReader
 └─ TextParser

Metadata Extractor
 └─ MetadataExtractor

Indexer
 ├─ Indexer
 ├─ DocumentMapper
 └─ DatabaseManager

Query Processor
 ├─ SearchService
 ├─ QueryProcessor
 └─ RankingService

Preview Generator
 └─ PreviewService
```

#### File Crawler
- `FileCrawler` – walks recursively through folders and finds files that can be indexed
- `FileScanner` – checks file type, path, and whether the file should be skipped

#### File Reader
- `FileReader` – opens files and reads their text content
- `TextParser` – cleans or formats the raw text before it is stored

#### Metadata Extractor
- `MetadataExtractor` – extracts metadata such as file name, extension, size, and timestamps

#### Indexer
- `Indexer` – coordinates the indexing process and sends processed data for storage
- `DocumentMapper` – transforms file content and metadata into a format that matches the database schema
- `DatabaseManager` – handles the connection to the database and executes insert or update operations

#### Query Processor
- `SearchService` – provides the main search operation used by the interface
- `QueryProcessor` – interprets the user query and prepares the search conditions
- `RankingService` – orders the results by relevance

#### Preview Generator
- `PreviewService` – generates data for a short preview or snippet for each matching result