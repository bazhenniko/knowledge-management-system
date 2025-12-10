const getApiUrl = (functionId: string) => {
  const isProd = import.meta.env.PROD;
  return isProd ? `/api/functions/${functionId}` : `https://functions.poehali.dev/${functionId}`;
};

export const API_CONFIG = {
  AUTH_API: import.meta.env.VITE_AUTH_API_URL || getApiUrl('af05cfe5-2869-458e-8c1b-998684e530d2'),
  DATABASE_INFO: import.meta.env.VITE_DATABASE_INFO_URL || getApiUrl('459a10f2-9dff-481a-af79-dcf6ca5cb628'),
  DATABASE_QUERY: import.meta.env.VITE_DATABASE_QUERY_URL || getApiUrl('d2daf71d-ad1e-4d8c-8fa3-7e5412c6727d'),
  DATABASE_MIGRATE: import.meta.env.VITE_DATABASE_MIGRATE_URL || getApiUrl('952351fb-9c3a-41c4-829d-53e0e293f957'),
  EXTERNAL_DB: import.meta.env.VITE_EXTERNAL_DB_URL || getApiUrl('5ce5a766-35aa-4d9a-9325-babec287d558'),
  FUNCTION_TRACKER: import.meta.env.VITE_FUNCTION_TRACKER_URL || getApiUrl('9af65be8-de12-472e-910f-fd63b3516ed9'),
  EMAIL_API: import.meta.env.VITE_EMAIL_API_URL || getApiUrl('75306ed7-e91c-4135-84fe-8b519f7dcf17'),
  PASSWORD_RESET: import.meta.env.VITE_PASSWORD_RESET_URL || getApiUrl('592a9eab-8102-4536-b07f-780566a0612b'),
} as const;