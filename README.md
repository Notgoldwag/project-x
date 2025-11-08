# Code Editor Interface

A VS Code-like editor interface that displays code with syntax highlighting.

## Configuration

The displayed code content is now **fully configurable**! You can easily change what appears in the editor by modifying the configuration at the top of the file.

### How to Change the Displayed Content

1. Open `index.html` in a text editor
2. Find the `editorConfig` object (around line 36)
3. Modify the properties as needed:
   - `filename`: The name displayed in the editor tab
   - `language`: The programming language (currently only affects the icon)
   - `content`: The actual code content to display

### Example Configuration

```javascript
const editorConfig = {
  filename: "index.html",
  language: "html",
  content: `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Awesome Page</title>
  </head>
  <body>
    <h1>Hello, World!</h1>
  </body>
</html>`
};
```

### Changing to Different Code

Want to display JavaScript instead? Just update the config:

```javascript
const editorConfig = {
  filename: "app.js",
  language: "javascript",
  content: `function greet(name) {
  console.log(\`Hello, \${name}!\`);
}

greet("World");`
};
```

The editor will automatically:
- Update the filename in the tab
- Adjust line numbers based on your content
- Apply syntax highlighting for HTML code

### Features

- ✅ Configurable filename
- ✅ Configurable code content
- ✅ Automatic line number generation
- ✅ HTML syntax highlighting
- ✅ Clean, VS Code-like interface

## Usage

Simply open `index.html` in a web browser to view the editor interface with your configured content.
