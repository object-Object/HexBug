import { StaffGrid, type StaffGridRef } from "@hextools/react";
import { useIsTouchscreen } from "@hextools/react";
import { useLocalStorageObject } from "@hextools/react";
import {
  GuiSpellcasting,
  DEFAULT_PATTERN_TYPE,
  type GuiSpellcastingSettings,
  type ResolvedPattern,
  HexDir,
} from "@hextools/renderer/staffGrid";
import { Box, Center, Image } from "@mantine/core";
import {
  useHotkeys,
  useStateHistory,
  useDebouncedCallback,
} from "@mantine/hooks";
import { useEffect, useRef } from "react";

import StaffGridControls from "./StaffGridControls";
import type { StaffGridSettingsProps } from "./StaffGridSettings";
import iconUrl from "./assets/icon.png";
import { useDiscordAuth, type AuthResult } from "./hooks/useDiscordAuth";
import {
  DiscordLayoutMode,
  useDiscordLayoutMode,
} from "./hooks/useDiscordLayoutMode";

export interface AppInnerProps extends Pick<
  StaffGridSettingsProps,
  "onSignInWithDiscord"
> {}

export default function AppInner({ onSignInWithDiscord }: AppInnerProps) {
  const layoutMode = useDiscordLayoutMode();
  const isUnfocused = layoutMode !== DiscordLayoutMode.FOCUSED;

  const isTouchscreen = useIsTouchscreen();

  const auth = useDiscordAuth();

  const [patterns, patternsHandlers, patternsHistory] = useStateHistory<
    ResolvedPattern[]
  >([]);

  const throttledPostPatterns = useDebouncedCallback(
    (auth: AuthResult, patterns: ResolvedPattern[]) => {
      void fetch("/api/activity/patterns", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${auth.api_token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          patterns.map(({ pattern }) => ({
            direction: HexDir[pattern.startDir],
            signature: pattern.anglesSignature(),
          })),
        ),
      });
    },
    { delay: 500 },
  );

  useEffect(() => {
    if (auth) {
      throttledPostPatterns(auth, patterns);
    }
  }, [auth, patterns, throttledPostPatterns]);

  const staffGridRef = useRef<StaffGridRef>(null);

  const defaultSettings = GuiSpellcasting.getDefaultSettings({
    isTouchscreen,
  });

  const [settings, setSettings] =
    useLocalStorageObject<GuiSpellcastingSettings>({
      key: "staff-grid-settings",
      defaultValue: defaultSettings,
    });

  useHotkeys([
    ["Escape", () => staffGridRef.current?.cancelPattern()],
    ["mod+Z", () => patternsHandlers.back()],
    ["mod+Y", () => patternsHandlers.forward()],
    ["mod+shift+Z", () => patternsHandlers.forward()],
  ]);

  return (
    <>
      <Box
        pos="relative"
        w="100%"
        h="100dvh"
        // Hide if unfocused, but still render the component
        display={isUnfocused ? "none" : undefined}
      >
        <StaffGrid
          patterns={patterns}
          onPatternsChange={patternsHandlers.set}
          patternType={DEFAULT_PATTERN_TYPE}
          settings={settings}
          ref={staffGridRef}
        />

        <StaffGridControls
          patterns={patterns}
          patternsHandlers={patternsHandlers}
          patternsHistory={patternsHistory}
          settings={settings}
          onSettingsChange={setSettings}
          onResetSettings={() => setSettings(defaultSettings)}
          onSignInWithDiscord={onSignInWithDiscord}
        />
      </Box>

      {isUnfocused && (
        <Center h="100dvh">
          <Image src={iconUrl} maw="50%" mah="50%" style={{ aspectRatio: 1 }} />
        </Center>
      )}
    </>
  );
}
