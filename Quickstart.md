# Quickstart Guide

Get TryAlma running in minutes and extract data from your first documents.

## Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** - Fast Python package manager
- **Anthropic API Key** - Required for G-28 form extraction

### Installing UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Getting an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to API Keys and create a new key
4. Copy the key for the next step

## Setup

### Step 1: Install Dependencies

```bash
uv sync
```

### Step 2: Set Your API Key

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your-api-key-here
```

Or export it directly in your terminal:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Step 3: Start the App

```bash
uv run flask --app tryalma.webapp.app:create_app run
```

You should see:

```
 * Running on http://127.0.0.1:5000
```

## Using the App

### Step 1: Open the App

Open your browser and go to:

```
http://localhost:5000
```

![Upload Interface](docs/images/upload-step1.png)

### Step 2: Upload a G-28 Form

1. Select **"G-28 Form"** from the Document Type dropdown
2. Drag and drop your G-28 PDF file, or click to browse
3. Click **"Upload Document"**

Wait for the extraction to complete. You'll see the extracted attorney and client information displayed on the right.

![Submit Document](docs/images/submit-step2.png)

### Step 3: Upload a Passport

1. Select **"Passport"** from the Document Type dropdown
2. Drag and drop your passport image (JPG, PNG, or PDF)
3. Click **"Upload Document"**

The passport data will be extracted and displayed alongside the G-28 data.

![Processing Documents](docs/images/submiting-step3.png)

### Step 4: Review Your Data

Both the G-28 and passport data are now displayed in the Extraction Results panel. The data persists even if you refresh the page.

![Success](docs/images/succes-step4.png)

Click **"Clear Results"** to start over with new documents.

## Using the CLI

TryAlma also provides two command-line tools for batch processing documents.

### Passport Extraction

Extract data from passport images using MRZ (Machine Readable Zone) OCR:

```bash
# Single file
uv run tryalma passport extract path/to/passport.jpg

# Entire directory
uv run tryalma passport extract path/to/images/

# Output as JSON
uv run tryalma passport extract path/to/passport.jpg --format json
```

### G-28 Form Parsing

Parse USCIS Form G-28 documents (requires Anthropic API key):

```bash
# Parse a G-28 form
uv run tryalma parse-g28 path/to/g28.pdf

# Output as JSON
uv run tryalma parse-g28 path/to/g28.pdf --format json
```

### Help

```bash
uv run tryalma --help
```

## Troubleshooting

**"Anthropic API key not configured" error**
- Make sure your `ANTHROPIC_API_KEY` environment variable is set
- Restart the Flask server after setting the variable

**Extraction failed**
- Ensure your document is clear and readable
- G-28 forms should be PDF format
- Passports work best as high-resolution images

**Port already in use**
- Run on a different port: `uv run flask --app tryalma.webapp.app:create_app run --port 5001`

## Next Steps

- See [README.md](README.md) for CLI usage and API documentation
- Check available datasets in [datasets/README.md](datasets/README.md)
