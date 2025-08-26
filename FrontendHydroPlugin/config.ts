export interface PhosphorusConfig {
  /** Base URL for the Phosphorus backend API */
  baseUrl: string;
  
  /** Request timeout in milliseconds */
  timeout: number;
  
  /** Enable debug logging */
  debug: boolean;
  
  /** Default analysis parameters */
  defaults: {
    minTokens: number;
    similarityThreshold: number;
  };
}

export const defaultConfig: PhosphorusConfig = {
  baseUrl: process.env.PHOSPHORUS_URL || 'http://localhost:8000',
  timeout: 30000,
  debug: process.env.NODE_ENV === 'development',
  defaults: {
    minTokens: 9,
    similarityThreshold: 0.0,
  },
};

export function getConfig(): PhosphorusConfig {
  return {
    ...defaultConfig,
    // Override with environment variables if provided
    baseUrl: process.env.PHOSPHORUS_URL || defaultConfig.baseUrl,
    timeout: parseInt(process.env.PHOSPHORUS_TIMEOUT || '30000', 10),
    debug: process.env.PHOSPHORUS_DEBUG === 'true' || defaultConfig.debug,
  };
}