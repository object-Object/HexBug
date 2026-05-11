import { StaffGrid, type StaffGridRef } from "@hextools/react";
import { useIsTouchscreen } from "@hextools/react";
import { useLocalStorageObject } from "@hextools/react";
import {
  GuiSpellcasting,
  type GuiSpellcastingSettings,
  type ResolvedPattern,
} from "@hextools/renderer/staffGrid";
import { Box } from "@mantine/core";
import { useHotkeys, useStateHistory } from "@mantine/hooks";
import { useRef } from "react";

import StaffGridControls from "./StaffGridControls";

export default function App() {
  const isTouchscreen = useIsTouchscreen();

  const [patterns, patternsHandlers, patternsHistory] = useStateHistory<
    ResolvedPattern[]
  >([]);

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
    <Box pos="relative" w="100%" h="100dvh">
      <StaffGrid
        patterns={patterns}
        onPatternsChange={patternsHandlers.set}
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
      />
    </Box>
  );
}
