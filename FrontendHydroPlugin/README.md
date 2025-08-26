# Hydro OJ Phosphorus Plugin

A Hydro OJ plugin that integrates with the Phosphorus backend for plagiarism detection using JPlag.

## Features

- Analyze contest submissions for plagiarism
- View detailed similarity reports
- Clustering of similar submissions
- Support for multiple programming languages
- Real-time analysis progress
- Administrative controls

## Prerequisites

1. **Hydro OJ** instance running
2. **Phosphorus backend** server running and accessible
3. **MongoDB** database with contest and submission data

## Installation

### 1. Install the Plugin

Copy this plugin directory to your Hydro OJ addons directory:

```bash
# If using Hydro OJ from npm
cp -r FrontendHydroPlugin /path/to/hydro/addons/CAUCOJ-Phosphorus

# If using Hydro OJ from source
cp -r FrontendHydroPlugin /path/to/hydrooj/addons/CAUCOJ-Phosphorus
```

### 2. Install Dependencies

Navigate to the plugin directory and install dependencies:

```bash
cd /path/to/hydro/addons/CAUCOJ-Phosphorus
npm install
```

### 3. Configure Phosphorus Backend URL

Set the environment variable for the Phosphorus backend:

```bash
export PHOSPHORUS_URL=http://localhost:8000
```

Or modify the `PHOSPHORUS_BASE_URL` constant in `index.ts` to point to your Phosphorus backend.

### 4. Enable the Plugin

Add the plugin to your Hydro OJ configuration. In your Hydro config file (usually `config.yaml` or through environment variables):

```yaml
addons:
  - CAUCOJ-Phosphorus
```

### 5. Restart Hydro OJ

Restart your Hydro OJ instance to load the plugin:

```bash
# If using pm2
pm2 restart hydro

# If using systemctl
systemctl restart hydro

# If running manually
# Stop and start your Hydro instance
```

## Usage

### For Contest Administrators

1. Navigate to any contest page
2. Go to the "Admin" section
3. Click on "Plagiarism Detection" in the navigation menu
4. Configure analysis parameters:
   - **Minimum Tokens**: Number of tokens that must match (default: 9)
   - **Similarity Threshold**: Minimum similarity percentage (default: 0.0)
5. Click "Start Plagiarism Analysis"
6. View results when analysis completes

### Understanding Results

- **High Similarity Pairs**: Shows pairs of submissions with high similarity
- **Clusters**: Groups of submissions that are similar to each other
- **Submission Statistics**: Details about each analyzed submission
- **Failed Submissions**: Submissions that couldn't be analyzed

### Color Coding

- 🔴 **Red badges**: High similarity (>70% avg, >80% max)
- 🟡 **Yellow badges**: Medium similarity (>50% avg, >60% max)
- 🔵 **Blue badges**: Low similarity

## Configuration

### Environment Variables

- `PHOSPHORUS_URL`: URL of the Phosphorus backend (default: `http://localhost:8000`)

### Backend Requirements

The plugin expects the Phosphorus backend to have these endpoints:

- `POST /api/v1/contest/plagiarism`: Start plagiarism analysis
- `GET /api/v1/contest/{contest_id}/plagiarism`: Get analysis results

## Permissions

The plugin requires the following Hydro OJ permissions:

- `PERM_VIEW_CONTEST_ADMIN`: To view plagiarism results
- `PERM_EDIT_CONTEST`: To start new analyses

## Troubleshooting

### Common Issues

1. **"Contest not found" error**
   - Ensure the contest ID is valid
   - Check database connectivity

2. **"Failed to start plagiarism analysis" error**
   - Verify Phosphorus backend is running
   - Check the `PHOSPHORUS_URL` configuration
   - Review Phosphorus backend logs

3. **Permission denied errors**
   - Ensure user has appropriate permissions
   - Check Hydro OJ permission configuration

4. **No results showing**
   - Check if the contest has accepted submissions
   - Verify minimum submission requirements (at least 2 per problem)
   - Check Phosphorus backend logs for errors

### Debug Mode

To enable debug logging, set the log level in your Hydro configuration:

```yaml
logger:
  level: debug
```

### Backend Health Check

Verify the Phosphorus backend is accessible:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "success": true,
  "message": "Service is healthy",
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00.000Z"
}
```

## API Integration

### Request Format

The plugin sends requests to Phosphorus in this format:

```json
{
  "contest_id": "string",
  "min_tokens": 9,
  "similarity_threshold": 0.0
}
```

### Response Format

Expected response from Phosphorus:

```json
{
  "success": true,
  "message": "Contest plagiarism check completed successfully",
  "data": {
    "analysis_id": "uuid",
    "contest_id": "string",
    "problem_id": 123,
    "total_submissions": 25,
    "total_comparisons": 300,
    "execution_time_ms": 5000,
    "high_similarity_pairs": [...],
    "clusters": [...],
    "submission_stats": [...],
    "failed_submissions": [...],
    "created_at": "2025-01-01T00:00:00.000Z"
  }
}
```

## Development

### File Structure

```
FrontendHydroPlugin/
├── index.ts                 # Main plugin entry point
├── package.json            # Plugin metadata and dependencies
├── templates/
│   └── contest_plagiarism.html  # Jinja2 template for UI
├── locales/
│   ├── en.json             # English translations
│   └── zh.json             # Chinese translations
└── README.md               # This file
```

### Building

If you modify the TypeScript files, you may need to recompile:

```bash
npm run build  # If build script is configured
# or
tsc index.ts   # Direct TypeScript compilation
```

### Testing

Test the plugin functionality:

1. Create a test contest with multiple submissions
2. Ensure submissions are accepted (status = 1)
3. Run plagiarism analysis
4. Verify results display correctly

## Support

For issues related to:

- **Plugin functionality**: Check this README and Hydro OJ documentation
- **Phosphorus backend**: Check the main Phosphorus repository
- **JPlag analysis**: Refer to JPlag documentation

## License

This plugin is licensed under GPL v3.0, same as the main Phosphorus project.