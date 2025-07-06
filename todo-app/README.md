# Todo List Application

A simple, elegant todo list application built with React and TypeScript. Features a modern UI with gradient styling and smooth animations.

## Features

✅ **Add new todos** - Type your task and press Enter or click "Add Todo"  
✅ **Mark as complete** - Click the checkbox to mark tasks as completed  
✅ **Delete todos** - Remove tasks you no longer need  
✅ **Persistent storage** - Your todos are saved in localStorage and persist across sessions  
✅ **Responsive design** - Works beautifully on desktop and mobile devices  
✅ **Modern UI** - Features gradient backgrounds, smooth animations, and hover effects  

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn

### Installation

1. Navigate to the project directory:
```bash
cd todo-app
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Usage

1. **Adding a Todo**: 
   - Type your task in the input field
   - Press Enter or click the "Add Todo" button

2. **Completing a Todo**:
   - Click the checkbox next to a task to mark it as complete
   - Completed tasks will show with a strikethrough

3. **Deleting a Todo**:
   - Click the "Delete" button to remove a task

4. **Data Persistence**:
   - All todos are automatically saved to localStorage
   - Your todos will be there when you refresh or revisit the page

## Technologies Used

- **React** - UI library
- **TypeScript** - Type safety and better developer experience
- **CSS3** - Modern styling with animations and gradients
- **localStorage** - Browser storage for data persistence

## Project Structure

```
src/
├── App.tsx          # Main app component
├── App.css          # Global styles
├── components/
│   └── Todo.tsx     # Todo list component
└── index.tsx        # Entry point
```

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm build` - Builds the app for production
- `npm test` - Runs the test suite
- `npm eject` - Ejects from Create React App (not recommended)

## Future Enhancements

- Edit existing todos
- Filter todos (All, Active, Completed)
- Due dates for todos
- Categories or tags
- Drag and drop to reorder
- Dark mode toggle

## License

This project is open source and available under the MIT License.
