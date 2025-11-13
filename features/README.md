# Features Directory

This directory contains refactored features from `home.html`, organized for better maintainability.

## Structure

Each feature follows this pattern:
```
features/<feature-name>/
  ├── template.html  # HTML markup
  ├── script.js      # JavaScript logic
  └── backend.py     # Python API handlers (if applicable)
```

## Completed Features

### ✅ authentication/
- **Purpose**: Handles Supabase authentication, session management, and redirects
- **Template**: Auth loading overlay
- **Script**: Auth check, login redirect, session handling
- **Dependencies**: Supabase client

### ✅ background_animation/
- **Purpose**: Animated fluid background with blobs and gradients
- **Template**: Background container and dimmer
- **Script**: Managed by React bundle (static/js/bundle.js)
- **Dependencies**: React TypeScript bundle

### ✅ cursor_glow/
- **Purpose**: Interactive cursor glow effect that follows mouse movement
- **Template**: Cursor glow element
- **Script**: Mouse tracking, smooth animation, accessibility support
- **Dependencies**: None

### ✅ navigation/
- **Purpose**: Left rail navigation with panel switching
- **Template**: Sidebar with editor, playground, and security buttons
- **Script**: Panel show/hide logic, button state management
- **Dependencies**: All panel features

### ✅ profile_widget/
- **Purpose**: User profile display in sidebar with sign-out
- **Template**: Profile avatar and popover
- **Script**: Managed by authentication feature
- **Dependencies**: Authentication feature

### ✅ prompt_injection/
- **Purpose**: Security scanner for detecting prompt injection attempts
- **Files**: backend.py, promptinjections.js (moved from static/js/)
- **Status**: Backend exists, frontend needs refactoring

### ✅ prompt_playground/
- **Purpose**: Multi-model AI comparison playground
- **Files**: backend.py, index.html, playground.js (moved from static/js/)
- **Status**: Backend exists, needs integration into features structure

### ✅ ai_assistant/
- **Purpose**: Chat interface with AI assistant
- **Files**: chat.js (moved from static/js/)
- **Status**: Needs template extraction and ChatManager refactoring

## Features Still in home.html (Inline)

These features are large and complex, marked for future refactoring:

### 🔄 history_panel/
- **Lines**: ~1200-1330, 3578-3900
- **Description**: Chat history sidebar with search, collapse, and Supabase integration
- **Complexity**: High - Supabase integration, search, state management
- **Priority**: High

### 🔄 text_editor/
- **Lines**: ~1332-1412
- **Description**: Formatted markdown editor with stats and actions
- **Complexity**: Medium - Markdown rendering, stats calculation
- **Priority**: High

### 🔄 ai_assistant (ChatManager)/
- **Lines**: ~3901-5333 (1400+ lines!)
- **Description**: Complete chat interface with ChatManager class
- **Complexity**: Very High - Message handling, scrolling, markdown rendering, Supabase sync
- **Priority**: High
- **Note**: This is the largest inline feature (~25% of home.html)

### 🔄 prompt_injections_panel/
- **Lines**: ~1415-1561, 1879-2071, 2243-3017, 3183-3578
- **Description**: Security scanner panel with analysis and Supabase integration
- **Complexity**: Very High - ML model integration, visualization, history management
- **Priority**: Medium

### 🔄 playground_panel/
- **Lines**: ~1562-1697, 5336-5856
- **Description**: Prompt playground panel with multi-model comparison
- **Complexity**: Very High - Chart.js integration, API calls, meta-analysis
- **Priority**: Medium

## Integration in home.html

To use refactored features in home.html:

```jinja2
<!-- Authentication -->
{% include 'features/authentication/template.html' %}

<!-- Background Animation -->
{% include 'features/background_animation/template.html' %}

<!-- Cursor Glow -->
{% include 'features/cursor_glow/template.html' %}

<!-- Navigation -->
{% include 'features/navigation/template.html' %}

<!-- Scripts -->
<script src="{{ url_for('static', filename='features/authentication/script.js') }}"></script>
<script src="{{ url_for('static', filename='features/cursor_glow/script.js') }}"></script>
<script src="{{ url_for('static', filename='features/navigation/script.js') }}"></script>
```

## Refactoring Guidelines

When extracting inline features:

1. **Identify boundaries**: Find clear start/end points in HTML
2. **Extract HTML**: Move to `template.html`
3. **Extract JavaScript**: Move to `script.js` with IIFE wrapper
4. **Maintain dependencies**: Document what each feature needs
5. **Test thoroughly**: Ensure no functionality breaks
6. **Update references**: Fix all IDs, class names, and imports

## Dependencies Graph

```
authentication
  └─> profile_widget

navigation
  ├─> text_editor (shows/hides)
  ├─> ai_assistant (shows/hides)
  ├─> prompt_injections_panel (shows/hides)
  └─> playground_panel (shows/hides)

ai_assistant (ChatManager)
  ├─> text_editor (updates content)
  ├─> history_panel (saves chats)
  └─> authentication (Supabase client)

history_panel
  └─> authentication (Supabase client)

prompt_injections_panel
  └─> authentication (Supabase client)
```

## File Organization

```
features/
├── ai_assistant/
│   ├── chat.js                 # n8n webhook integration
│   ├── template.html           # TODO: Extract from home.html lines 1698-1830
│   └── script.js               # TODO: Extract ChatManager class (lines 3901-5333)
├── authentication/
│   ├── script.js               # ✅ Complete
│   └── template.html           # ✅ Complete
├── background_animation/
│   ├── script.js               # ✅ Complete
│   └── template.html           # ✅ Complete
├── cursor_glow/
│   ├── script.js               # ✅ Complete
│   └── template.html           # ✅ Complete
├── history_panel/
│   ├── template.html           # TODO: Extract from home.html
│   └── script.js               # TODO: Extract history management logic
├── navigation/
│   ├── script.js               # ✅ Complete
│   └── template.html           # ✅ Complete
├── profile_widget/
│   ├── script.js               # ✅ Complete (minimal, managed by auth)
│   └── template.html           # ✅ Complete
├── prompt_injection/
│   ├── backend.py              # ✅ Exists
│   ├── promptinjections.js     # ✅ Moved from static/js/
│   ├── template.html           # TODO: Extract panel HTML
│   └── script.js               # TODO: Extract inline JS
└── prompt_playground/
    ├── backend.py              # ✅ Exists
    ├── index.html              # ✅ Exists (standalone page)
    ├── playground.js           # ✅ Moved from static/js/
    ├── template.html           # TODO: Extract panel HTML
    └── script.js               # TODO: Extract initialization function
```

## Next Steps

1. **High Priority**: Extract ChatManager class (ai_assistant/script.js)
2. **High Priority**: Extract history panel (history_panel/)
3. **High Priority**: Extract text editor (text_editor/)
4. **Medium Priority**: Extract prompt injections panel
5. **Medium Priority**: Extract playground panel
6. **Low Priority**: Consolidate CSS into feature-specific files

## Testing Checklist

After each feature extraction:
- [ ] Authentication flow works
- [ ] Navigation switches between panels correctly
- [ ] Editor displays and updates content
- [ ] Chat sends/receives messages
- [ ] History loads and searches
- [ ] Security scanner analyzes prompts
- [ ] Playground compares models
- [ ] No console errors
- [ ] No broken references
- [ ] UI matches original appearance
