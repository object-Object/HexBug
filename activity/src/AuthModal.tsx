import {
  Modal,
  Title,
  Text,
  Code,
  Stack,
  Button,
  Group,
  Loader,
} from "@mantine/core";

import {
  AuthState,
  type UseDiscordAuthStateResult,
} from "./hooks/useDiscordAuth";

export interface AuthModalProps extends Pick<
  UseDiscordAuthStateResult,
  "authState" | "onAuthStateChange" | "isPending"
> {}

export default function AuthModal({
  authState,
  onAuthStateChange,
  isPending,
}: AuthModalProps) {
  return (
    <Modal.Root
      opened={
        authState === AuthState.none || authState === AuthState.authenticating
      }
      onClose={() => null}
    >
      <Modal.Overlay />
      <Modal.Content>
        <Modal.Body>
          <Stack align="center" gap="xs">
            <Title size="h2">Sign in with Discord?</Title>
            <Text c="dimmed">
              This is required for commands like <Code>/patterns draw</Code>.
            </Text>
            {isPending ? (
              <Loader />
            ) : (
              <Group>
                <Button
                  onClick={() => onAuthStateChange(AuthState.authenticating)}
                >
                  Yes
                </Button>
                <Button
                  onClick={() => onAuthStateChange(AuthState.denied)}
                  variant="default"
                >
                  No
                </Button>
              </Group>
            )}
          </Stack>
        </Modal.Body>
      </Modal.Content>
    </Modal.Root>
  );
}
