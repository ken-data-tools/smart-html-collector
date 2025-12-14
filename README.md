# Smart HTML Collector

Automation tool that accesses given URLs and saves the rendered HTML files as-is.

## Features
- Browser-like headers
- Randomized access intervals
- HTML saving per URL
- Failure logging (CSV)

## How it works (Overview)
1. Read URLs from a CSV file
2. Access each URL with a request header
3. Save the HTML response into an output folder
4. Record failures for retry
