import React from 'react';

const LoadingSpinner = ({ message = '加载中...', size = 'medium' }) => {
  const spinnerSize = size === 'small' ? '1rem' : size === 'large' ? '3rem' : '2rem';
  
  return (
    <div className="text-center my-4">
      <div 
        className="spinner-border" 
        role="status"
        style={{ 
          width: spinnerSize, 
          height: spinnerSize,
          borderWidth: size === 'small' ? '0.2em' : '0.25em'
        }}
      >
        <span className="visually-hidden">加载中...</span>
      </div>
      {message && <p className="mt-2">{message}</p>}
    </div>
  );
};

export default LoadingSpinner; 