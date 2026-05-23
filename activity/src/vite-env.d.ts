// https://vite.dev/guide/env-and-mode#intellisense-for-typescript

interface ViteTypeOptions {
  strictImportMetaEnv: unknown;
}

interface ImportMetaEnv {
  readonly VITE_CLIENT_ID: string;
  readonly VITE_JWT_PUBLIC_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
