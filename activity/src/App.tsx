import { LoadingOverlay } from "@mantine/core";
import { Suspense } from "react";

import AppInner from "./AppInner";
import AuthModal from "./AuthModal";
import { AuthState, useDiscordAuthState } from "./hooks/useDiscordAuth";

export default function App() {
  const {
    auth: _auth,
    authState,
    onAuthStateChange,
    isPending,
  } = useDiscordAuthState();

  const handleSignInWithDiscord = () => onAuthStateChange(AuthState.accepted);

  return (
    <>
      <Suspense
        fallback={
          <LoadingOverlay visible overlayProps={{ bg: "transparent" }} />
        }
      >
        <AppInner
          onSignInWithDiscord={
            authState !== AuthState.accepted ? handleSignInWithDiscord : null
          }
        />
      </Suspense>

      <AuthModal
        authState={authState}
        onAuthStateChange={onAuthStateChange}
        isPending={isPending}
      />
    </>
  );
}
