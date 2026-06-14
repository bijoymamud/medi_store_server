import express, { Application, Request, Response } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import globalErrorHandler from './middlewares/globalErrorHandler';
import notFound from './middlewares/notFound';

const app: Application = express();

// Parsers
app.use(express.json());
app.use(cors());

// Security and Logging
app.use(helmet());
app.use(morgan('dev'));

// Health check endpoint
app.get('/', (req: Request, res: Response) => {
  res.status(200).json({
    success: true,
    message: 'MediStore API is running smoothly',
  });
});

// Application routes will be added here
// app.use('/api/v1', router);

// Handle Not Found
app.use(notFound);

// Global Error Handler
app.use(globalErrorHandler);

export default app;
