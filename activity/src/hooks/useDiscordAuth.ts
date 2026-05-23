import type { DiscordSDK } from "@discord/embedded-app-sdk";
import { useLocalStorage } from "@mantine/hooks";
import * as jose from "jose";
import { startTransition, use, useActionState, useEffect } from "react";

import { discordSDKPromise } from "./useDiscordSDK";

export enum AuthState {
  none = "none",
  authenticating = "authenticating",
  accepted = "accepted",
  denied = "denied",
}

export type AuthResult = Awaited<AuthenticatePromise>;

export function useDiscordAuth(): AuthResult {
  const [authState] = useAuthState();

  return authState !== AuthState.denied && authPromise
    ? use(authPromise)
    : null;
}

export interface UseDiscordAuthStateResult {
  auth: AuthResult;
  authState: AuthState;
  onAuthStateChange: (authState: AuthState) => unknown;
  isPending: boolean;
}

export function useDiscordAuthState(): UseDiscordAuthStateResult {
  const [authState, setAuthState] = useAuthState();

  const [auth, dispatchAction, isPending] = useActionState<AuthResult | null>(
    async (prev) => {
      if (prev) {
        return prev;
      }
      authPromise ??= authenticate(await discordSDKPromise);
      const auth = await authPromise;
      if (auth) {
        setAuthState(AuthState.accepted);
      } else {
        setAuthState(AuthState.denied);
      }
      return auth;
    },
    null,
  );

  useEffect(() => {
    if (
      (authState === AuthState.authenticating
        || authState === AuthState.accepted)
      && !auth
    ) {
      startTransition(dispatchAction);
    }
  }, [auth, authState, dispatchAction]);

  return {
    auth,
    authState,
    onAuthStateChange: setAuthState,
    isPending,
  };
}

function useAuthState() {
  return useLocalStorage({
    key: "use-discord-auth-state",
    defaultValue: AuthState.none,
  });
}

let authPromise: AuthenticatePromise | null = null;

const publicKeyPromise = jose.importSPKI(
  import.meta.env.VITE_JWT_PUBLIC_KEY,
  "Ed25519",
);

// Keep in sync with bot/src/HexBug/cogs/api.py
interface ActivityTokenRequest {
  code: string;
}

// Keep in sync with bot/src/HexBug/cogs/api.py
interface ActivityTokenResponse {
  access_token: string;
  api_token: string;
}

// Keep in sync with bot/src/HexBug/cogs/api.py
interface ActivityAPIToken {
  user_id: string;
}

type AuthenticatePromise = ReturnType<typeof authenticate>;

async function authenticate(discordSDK: DiscordSDK) {
  let authOutput;
  try {
    authOutput = await discordSDK.commands.authorize({
      client_id: import.meta.env.VITE_CLIENT_ID,
      response_type: "code",
      prompt: "none",
      scope: ["identify"],
    });
  } catch (err) {
    // Usually this means the user cancelled the authorization
    console.warn("Authorization failed", err);
    return null;
  }

  const tokenResponse = await fetch("/api/activity/token", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(authOutput satisfies ActivityTokenRequest),
  });
  if (!tokenResponse.ok) {
    throw new Error(`Login request failed: ${tokenResponse.status}`);
  }

  const { access_token, api_token } =
    (await tokenResponse.json()) as ActivityTokenResponse;

  const publicKey = await publicKeyPromise;
  const decryptResult = await jose.jwtVerify<ActivityAPIToken>(
    api_token,
    publicKey,
  );
  const api_token_value: ActivityAPIToken = decryptResult.payload;

  const authResponse = await discordSDK.commands.authenticate({
    access_token,
  });

  if (api_token_value.user_id !== authResponse.user.id) {
    throw new Error(
      `Mismatched user id in API token: expected ${authResponse.user.id}, got ${api_token_value.user_id}`,
    );
  }

  return {
    api_token,
    api_token_value,
    ...authResponse,
  };
}
