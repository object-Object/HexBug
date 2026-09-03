import { StaffGrid, type StaffGridRef } from "@hextools/react";
import { useIsTouchscreen } from "@hextools/react";
import { useLocalStorageObject } from "@hextools/react";
import {
  GuiSpellcasting,
  DEFAULT_PATTERN_TYPE,
  type GuiSpellcastingSettings,
  type ResolvedPattern,
  HexDir,
  PATTERN_TYPES,
} from "@hextools/renderer/staffGrid";
import { Box, Center, Image } from "@mantine/core";
import {
  useHotkeys,
  useStateHistory,
  useDebouncedCallback,
} from "@mantine/hooks";
import { useEffect, useMemo, useRef, useState } from "react";

import StaffGridControls from "./StaffGridControls";
import type { StaffGridSettingsProps } from "./StaffGridSettings";
import { postActivityPatterns, type ActivityHexPattern } from "./api";
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
    readonly ResolvedPattern[]
  >([]);

  const [resolvedPatternsCache, setResolvedPatternsCache] = useState<
    Partial<Record<string, string | null>>
  >({});

  const [patternType, setPatternType] = useState(DEFAULT_PATTERN_TYPE);

  const resolvedPatterns = useMemo(
    () =>
      patterns.map((pattern): ResolvedPattern => {
        if (pattern.type === PATTERN_TYPES.Escaped) {
          return pattern;
        }
        const name =
          resolvedPatternsCache[
            `${HexDir[pattern.pattern.startDir]} ${pattern.pattern.signature}`
          ];
        switch (name) {
          case undefined:
            return { ...pattern, type: PATTERN_TYPES.Unresolved };
          case null:
            return { ...pattern, type: PATTERN_TYPES.Invalid };
          default:
            return { ...pattern, type: PATTERN_TYPES.Evaluated, name };
        }
      }),
    [patterns, resolvedPatternsCache],
  );

  const throttledPostPatterns = useDebouncedCallback(
    async (auth: AuthResult, patterns: readonly ResolvedPattern[]) => {
      const result = await postActivityPatterns({
        patterns: patterns.map(({ pattern }) => ({
          direction: HexDir[
            pattern.startDir
          ] as ActivityHexPattern["direction"],
          signature: pattern.signature,
          lookup: !(
            `${HexDir[pattern.startDir]} ${pattern.signature}`
            in resolvedPatternsCache
          ),
        })),
        api_token: auth.api_token,
      });

      setResolvedPatternsCache((prev) => ({
        ...prev,
        ...Object.fromEntries(
          result.map(({ direction, signature, name }) => [
            `${direction} ${signature}`,
            name,
          ]),
        ),
      }));
    },
    { delay: 250 },
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

  const onPanToPattern = (pattern: ResolvedPattern) => {
    staffGridRef.current?.panToPattern(pattern);
  };

  const onResetPanAndZoom = () => {
    staffGridRef.current?.resetPanAndZoom();
  };

  return (
    <>
      <Box
        pos="relative"
        w="100%"
        h="100dvh"
        // Hide if unfocused, but still render the component
        display={isUnfocused ? "none" : undefined}
        style={{
          overflow: "hidden",
        }}
      >
        <StaffGrid
          patterns={resolvedPatterns}
          onPatternsChange={patternsHandlers.set}
          patternType={patternType}
          onPatternTypeChange={setPatternType}
          settings={settings}
          ref={staffGridRef}
        />

        <StaffGridControls
          patterns={resolvedPatterns}
          patternsHandlers={patternsHandlers}
          patternsHistory={patternsHistory}
          settings={settings}
          onSettingsChange={setSettings}
          onResetSettings={() => setSettings(defaultSettings)}
          onSignInWithDiscord={onSignInWithDiscord}
          onPanToPattern={onPanToPattern}
          onResetPanAndZoom={onResetPanAndZoom}
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
