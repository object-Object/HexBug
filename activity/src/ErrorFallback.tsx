import { Button, Center, Code, Stack, Title } from "@mantine/core";
import { getErrorMessage, type FallbackProps } from "react-error-boundary";

export default function ErrorFallback({
  error,
  resetErrorBoundary,
}: FallbackProps) {
  return (
    <Center h="100dvh">
      <Stack align="center">
        <Title size="h2">Something went wrong :(</Title>
        <Code block w="100%">
          {getErrorMessage(error)}
        </Code>
        <Button variant="default" onClick={resetErrorBoundary}>
          Retry
        </Button>
      </Stack>
    </Center>
  );
}
