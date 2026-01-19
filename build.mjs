/**
 * Build script for widget bundles
 * 
 * Creates standalone HTML files with embedded JS and CSS for each widget.
 */

import * as esbuild from 'esbuild';
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

const widgets = [
  { name: 'photo-upload', entry: 'src/widgets/PhotoUpload.jsx' },
  { name: 'results', entry: 'src/widgets/Results.jsx' },
  { name: 'timeline', entry: 'src/widgets/Timeline.jsx' },
];

// Create assets directory
const assetsDir = join(__dirname, '../assets');
try {
  mkdirSync(assetsDir, { recursive: true });
} catch (e) {
  // Directory might already exist
}

console.log('🔨 Building widgets...\n');

for (const widget of widgets) {
  console.log(`Building ${widget.name}...`);

  try {
    // Build the widget bundle
    const result = await esbuild.build({
      entryPoints: [widget.entry],
      bundle: true,
      format: 'iife',
      globalName: 'Widget',
      jsx: 'automatic',
      minify: true,
      write: false,
      loader: {
        '.js': 'jsx',
        '.jsx': 'jsx',
      },
    });

    const jsCode = result.outputFiles[0].text;

    // Create standalone HTML file
    const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${widget.name}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background: #ffffff; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script>
    ${jsCode}
    
    // Mount the widget
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(React.createElement(Widget.default || Widget));
  </script>
</body>
</html>`;

    // Write HTML file
    const outputPath = join(assetsDir, `${widget.name}.html`);
    writeFileSync(outputPath, html);

    console.log(`✅ ${widget.name}.html created`);
  } catch (error) {
    console.error(`❌ Failed to build ${widget.name}:`, error);
  }
}

console.log('\n✨ Build complete!');
