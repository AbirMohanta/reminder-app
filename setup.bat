@echo off
echo Checking and creating directories...

REM Create virtual environment if it doesn't exist
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing Python requirements...
pip install -r requirements.txt

REM Check if frontend directory exists
if not exist frontend (
    echo Creating new React application...
    npx create-react-app frontend --template typescript
)

echo Installing frontend dependencies...
cd frontend
call npm install @mui/material @emotion/react @emotion/styled
call npm install @mui/icons-material
call npm install @mui/x-date-pickers dayjs
call npm install axios

echo Creating necessary frontend files...

REM Create public/index.html
echo Creating index.html...
(
echo ^<!DOCTYPE html^>
echo ^<html lang="en"^>
echo   ^<head^>
echo     ^<meta charset="utf-8" /^>
echo     ^<link rel="icon" href="%PUBLIC_URL%/favicon.ico" /^>
echo     ^<meta name="viewport" content="width=device-width, initial-scale=1" /^>
echo     ^<meta name="theme-color" content="#000000" /^>
echo     ^<meta name="description" content="Reminder Application" /^>
echo     ^<link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" /^>
echo     ^<link rel="manifest" href="%PUBLIC_URL%/manifest.json" /^>
echo     ^<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:300,400,500,700&display=swap" /^>
echo     ^<title^>Reminder App^</title^>
echo   ^</head^>
echo   ^<body^>
echo     ^<noscript^>You need to enable JavaScript to run this app.^</noscript^>
echo     ^<div id="root"^>^</div^>
echo   ^</body^>
echo ^</html^>
) > public\index.html

REM Create src/index.tsx
echo Creating index.tsx...
(
echo import React from 'react';
echo import ReactDOM from 'react-dom/client';
echo import App from './App';
echo import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
echo.
echo const theme = createTheme({
echo   palette: {
echo     mode: 'light',
echo     primary: {
echo       main: '#1976d2',
echo     },
echo     secondary: {
echo       main: '#dc004e',
echo     },
echo   },
echo });
echo.
echo const root = ReactDOM.createRoot^(
echo   document.getElementById^('root'^) as HTMLElement
echo ^);
echo.
echo root.render^(
echo   ^<React.StrictMode^>
echo     ^<ThemeProvider theme={theme}^>
echo       ^<CssBaseline /^>
echo       ^<App /^>
echo     ^</ThemeProvider^>
echo   ^</React.StrictMode^>
echo ^);
) > src\index.tsx

REM Create src/App.tsx
echo Creating App.tsx...
(
echo import React from 'react';
echo import { Container, Typography, Box } from '@mui/material';
echo import ReminderForm from './components/ReminderForm';
echo.
echo const App: React.FC = ^(^) =^> {
echo   return ^(
echo     ^<Container maxWidth="md"^>
echo       ^<Box sx={{ my: 4 }}^>
echo         ^<Typography variant="h4" component="h1" gutterBottom align="center"^>
echo           Reminder Application
echo         ^</Typography^>
echo         ^<ReminderForm /^>
echo       ^</Box^>
echo     ^</Container^>
echo   ^);
echo };
echo.
echo export default App;
) > src\App.tsx

REM Create components directory and ReminderForm.tsx
if not exist src\components mkdir src\components

echo Creating ReminderForm.tsx...
(
echo import React, { useState } from 'react';
echo import {
echo   Box,
echo   TextField,
echo   Button,
echo   Typography,
echo   Paper,
echo   Stack,
echo   Alert,
echo   Snackbar
echo } from '@mui/material';
echo import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
echo import { LocalizationProvider, DatePicker } from '@mui/x-date-pickers';
echo import dayjs, { Dayjs } from 'dayjs';
echo import axios from 'axios';
echo.
echo const API_BASE_URL = 'http://localhost:5001';
echo.
echo const ReminderForm: React.FC = ^(^) =^> {
echo   const [date, setDate] = useState^<Dayjs ^| null^>^(null^);
echo   const [description, setDescription] = useState^(''^);
echo   const [email, setEmail] = useState^(''^);
echo   const [loading, setLoading] = useState^(false^);
echo   const [snackbar, setSnackbar] = useState^({
echo     open: false,
echo     message: '',
echo     severity: 'success' as 'success' ^| 'error'
echo   }^);
echo.
echo   const handleSubmit = async ^(e: React.FormEvent^) =^> {
echo     e.preventDefault^(^);
echo     if ^(!date ^|^| ^!description ^|^| ^!email^) return;
echo.
echo     setLoading^(true^);
echo     try {
echo       const formData = new FormData^(^);
echo       formData.append^('date', date.format^('YYYY-MM-DD'^)^);
echo       formData.append^('description', description^);
echo       formData.append^('email', email^);
echo.
echo       const response = await axios.post^(`${API_BASE_URL}/add_reminder`, formData^);
echo       
echo       if ^(response.data.status === 'success'^) {
echo         setSnackbar^({
echo           open: true,
echo           message: 'Reminder added successfully!',
echo           severity: 'success'
echo         }^);
echo         setDate^(null^);
echo         setDescription^(''^);
echo       } else {
echo         throw new Error^(response.data.message^);
echo       }
echo     } catch ^(error^) {
echo       setSnackbar^({
echo         open: true,
echo         message: 'Failed to add reminder',
echo         severity: 'error'
echo       }^);
echo     } finally {
echo       setLoading^(false^);
echo     }
echo   };
echo.
echo   return ^(
echo     ^<LocalizationProvider dateAdapter={AdapterDayjs}^>
echo       ^<Paper elevation={3} sx={{ p: 3 }}^>
echo         ^<Typography variant="h6" gutterBottom^>
echo           Add New Reminder
echo         ^</Typography^>
echo         ^<Box component="form" onSubmit={handleSubmit}^>
echo           ^<Stack spacing={3}^>
echo             ^<DatePicker
echo               label="Date"
echo               value={date}
echo               onChange={^(newDate^) =^> setDate^(newDate^)}
echo               disablePast
echo             /^>
echo             ^<TextField
echo               label="Description"
echo               value={description}
echo               onChange={^(e^) =^> setDescription^(e.target.value^)}
echo               multiline
echo               rows={2}
echo               required
echo             /^>
echo             ^<TextField
echo               type="email"
echo               label="Email"
echo               value={email}
echo               onChange={^(e^) =^> setEmail^(e.target.value^)}
echo               required
echo             /^>
echo             ^<Button
echo               type="submit"
echo               variant="contained"
echo               disabled={loading ^|^| ^!date ^|^| ^!description ^|^| ^!email}
echo             ^>
echo               {loading ? 'Adding...' : 'Add Reminder'}
echo             ^</Button^>
echo           ^</Stack^>
echo         ^</Box^>
echo         ^<Snackbar
echo           open={snackbar.open}
echo           autoHideDuration={6000}
echo           onClose={^(^) =^> setSnackbar^({ ...snackbar, open: false }^)}
echo         ^>
echo           ^<Alert severity={snackbar.severity}^>
echo             {snackbar.message}
echo           ^</Alert^>
echo         ^</Snackbar^>
echo       ^</Paper^>
echo     ^</LocalizationProvider^>
echo   ^);
echo };
echo.
echo export default ReminderForm;
) > src\components\ReminderForm.tsx

cd ..

echo Setup complete!
echo.
echo To start the application:
echo 1. Start backend: python app.py
echo 2. Start frontend: cd frontend ^& npm start
echo.
echo Don't forget to update your .env file with your email settings!
pause 