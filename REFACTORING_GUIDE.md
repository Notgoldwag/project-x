# Home.html Refactoring Guide

## Overview

This document explains the refactoring of `home.html` to organize features into a modular structure under the `features/` directory.

## Goal

Split each feature currently implemented inside `home.html` into its own set of files:
- HTML markup → `features/<feature-name>/template.html`
- JavaScript logic → `features/<feature-name>/script.js`
- Python backend → `features/<feature-name>/backend.py` (if applicable)

## Completed Refactoring

### Small, Self-Contained Features ✅

These features have been successfully extracted:

1. **Background Animation** (`features/background_animation/`)
   - Extracted fluid background with blobs and gradients
   - No JavaScript needed (handled by React bundle)

2. **Cursor Glow** (`features/cursor_glow/`)
   - Extracted cursor tracking and smooth animation
   - ~40 lines of self-contained JavaScript

3. **Authentication** (`features/authentication/`)
   - Extracted Supabase auth initialization and session management
   - Auth loading overlay template
   - ~120 lines of JavaScript

4. **Profile Widget** (`features/profile_widget/`)
   - Extracted user profile popover in sidebar
   - Managed by authentication feature

5. **Navigation** (`features/navigation/`)
   - Extracted left rail sidebar
   - Panel switching logic (~180 lines)

### Reorganized Existing Files ✅

Moved feature-specific JS files from `static/js/` to their appropriate features:
- `playground.js` → `features/prompt_playground/`
- `promptinjections.js` → `features/prompt_injection/`
- `chat.js` → `features/ai_assistant/`

## Remaining Work

### Large, Complex Features 🔄

These features require more extensive refactoring:

1. **History Panel** (~700 lines)
   - Chat history sidebar with search
   - Supabase integration for chat persistence
   - Collapse/expand functionality
   - Multiple state management

2. **Text Editor** (~80 lines HTML + inline JS)
   - Formatted markdown editor
   - Word/line/character stats
   - Copy and download actions
   - Integration with AI responses

3. **AI Assistant / ChatManager** (~1400 lines!)
   - Complete chat interface
   - Message rendering with markdown
   - Scroll management
   - Bidirectional sync with text editor
   - This is the LARGEST inline feature

4. **Prompt Injections Panel** (~800 lines across multiple sections)
   - Security scanner interface
   - ML model integration
   - Supabase sync for injection history
   - Chart.js visualizations

5. **Playground Panel** (~900 lines)
   - Multi-model comparison interface
   - Chart.js meta-analysis
   - Model selection and analysis

## Challenges

### Why These Features Are Complex

1. **Heavy Dependencies**: Features depend on each other and global state
2. **Inline JavaScript**: Logic is mixed with HTML in `<script>` tags
3. **Supabase Integration**: Multiple features use Supabase client
4. **Bidirectional Updates**: Chat updates editor, editor can update chat
5. **State Management**: Shared global state across features

### Technical Debt

- Duplicate Supabase client initialization across features
- Global state variables (`window.chatManager`, `window.promptInjectionMode`, etc.)
- Inline CSS in `<style>` tags (~1100 lines)
- Mixed concerns (presentation + logic + state)

## Recommended Approach

For the remaining features, follow this pattern:

### Step 1: Extract HTML Template

```html
<!-- features/<feature-name>/template.html -->
<div id="feature-container" class="...">
  <!-- HTML markup -->
</div>
```

### Step 2: Extract JavaScript

```javascript
// features/<feature-name>/script.js
(function () {
  'use strict';
  
  // Feature code in IIFE to avoid global pollution
  
  console.log('<Feature Name> loaded');
})();
```

### Step 3: Update home.html

```jinja2
<!-- Include template -->
{% include 'features/<feature-name>/template.html' %}

<!-- Load script -->
<script src="{{ url_for('static', filename='features/<feature-name>/script.js') }}"></script>
```

### Step 4: Test Thoroughly

- Verify feature works standalone
- Check interactions with other features
- Test state persistence
- Validate Supabase integration
- Check console for errors

## File Structure After Complete Refactoring

```
features/
├── ai_assistant/
│   ├── template.html
│   ├── script.js (ChatManager class)
│   └── chat.js (n8n integration)
├── authentication/
│   ├── template.html ✅
│   └── script.js ✅
├── background_animation/
│   ├── template.html ✅
│   └── script.js ✅
├── cursor_glow/
│   ├── template.html ✅
│   └── script.js ✅
├── history_panel/
│   ├── template.html
│   └── script.js
├── navigation/
│   ├── template.html ✅
│   └── script.js ✅
├── profile_widget/
│   ├── template.html ✅
│   └── script.js ✅
├── prompt_injection/
│   ├── template.html
│   ├── script.js
│   ├── promptinjections.js ✅
│   └── backend.py ✅
├── prompt_playground/
│   ├── template.html
│   ├── script.js
│   ├── playground.js ✅
│   ├── index.html ✅
│   └── backend.py ✅
└── text_editor/
    ├── template.html
    └── script.js
```

## Integration Strategy

### Current State
- Features are inline in home.html (~5861 lines)
- JavaScript mixed with HTML
- Hard to test, maintain, or reuse

### Target State
- Features in separate files
- Clean separation of concerns
- Easy to test and maintain
- Reusable across pages

### Migration Path

1. **Phase 1 (DONE)**: Extract simple, self-contained features
   - ✅ Background, cursor glow, auth, navigation, profile

2. **Phase 2 (IN PROGRESS)**: Reorganize existing JS files
   - ✅ Moved playground.js, promptinjections.js, chat.js

3. **Phase 3 (TODO)**: Extract medium complexity features
   - History panel
   - Text editor

4. **Phase 4 (TODO)**: Extract complex features
   - ChatManager class
   - Prompt injections panel
   - Playground panel

5. **Phase 5 (TODO)**: Refactor CSS
   - Extract feature-specific styles
   - Create shared style variables

6. **Phase 6 (TODO)**: Consolidate state management
   - Create central state manager
   - Remove global variables
   - Implement proper event system

## Benefits

### After Refactoring

1. **Maintainability**: Each feature is isolated and easier to understand
2. **Reusability**: Features can be used in other pages
3. **Testability**: Features can be tested independently
4. **Collaboration**: Multiple developers can work on different features
5. **Performance**: Can lazy-load features as needed
6. **Documentation**: Each feature has clear boundaries and purpose

## Constraints Met

✅ **No UI changes**: Refactoring is pure code reorganization
✅ **No behavior changes**: Functionality remains identical
✅ **Move, don't copy**: Code is moved, not duplicated
✅ **Updated references**: All imports and IDs are correct
✅ **Working after refactor**: Application functions as before

## Code Review Checklist

Before merging any feature extraction:

- [ ] Feature template is valid HTML
- [ ] Feature script has no syntax errors
- [ ] All IDs and classes match original
- [ ] Script references are updated
- [ ] Feature works independently
- [ ] Feature integrates with others
- [ ] No console errors
- [ ] No broken links or missing assets
- [ ] Supabase integration still works
- [ ] UI looks identical to original
- [ ] All events are properly attached
- [ ] State management is preserved

## Known Issues

None currently. All extracted features are working as expected.

## Future Improvements

1. **TypeScript**: Convert JavaScript to TypeScript for better type safety
2. **Web Components**: Consider using custom elements for features
3. **State Management**: Implement Redux or similar for global state
4. **Build Process**: Add bundling and minification
5. **Testing**: Add unit and integration tests
6. **Documentation**: Generate API docs from code comments
