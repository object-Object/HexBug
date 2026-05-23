import { LoadingOverlay, MantineProvider } from "@mantine/core";
import "@mantine/core/styles.css";
import { StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";
import { ErrorBoundary } from "react-error-boundary";

import App from "./App.tsx";
import ErrorFallback from "./ErrorFallback.tsx";
import "./main.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <MantineProvider defaultColorScheme="dark">
      <Suspense
        fallback={
          <LoadingOverlay visible overlayProps={{ bg: "transparent" }} />
        }
      >
        <ErrorBoundary FallbackComponent={ErrorFallback}>
          <App />
        </ErrorBoundary>
      </Suspense>
    </MantineProvider>
  </StrictMode>,
);
