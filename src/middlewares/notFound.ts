import { Request, Response, NextFunction } from 'express';
import httpStatus from 'http-status'; // need to install http-status maybe later, but I will use 404 directly for now

const notFound = (req: Request, res: Response, next: NextFunction) => {
  res.status(404).json({
    success: false,
    message: 'API Not Found',
    error: {
      path: req.originalUrl,
      message: 'Your requested path is not found!',
    },
  });
};

export default notFound;
