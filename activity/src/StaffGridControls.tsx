import { ColorSchemeButton, StaffGridSidebar } from "@hextools/react";
import {
  type GuiSpellcastingSettings,
  type ResolvedPattern,
} from "@hextools/renderer/staffGrid";
import { ActionIcon, Stack } from "@mantine/core";
import {
  useDisclosure,
  type UseStateHistoryHandlers,
  type UseStateHistoryValue,
} from "@mantine/hooks";
import {
  IconArrowBackUp,
  IconArrowForwardUp,
  IconMenu2,
  IconTrash,
} from "@tabler/icons-react";

import { staffGridButtonProps } from "./StaffGridControls.lib";
import StaffGridSettings from "./StaffGridSettings";

export interface StaffGridControlsProps {
  patterns: ResolvedPattern[];
  patternsHandlers: UseStateHistoryHandlers<ResolvedPattern[]>;
  patternsHistory: UseStateHistoryValue<ResolvedPattern[]>;
  settings: GuiSpellcastingSettings;
  onSettingsChange: (settings: GuiSpellcastingSettings) => unknown;
  onResetSettings: () => unknown;
}

export default function StaffGridControls({
  patterns,
  patternsHandlers,
  patternsHistory,
  settings,
  onSettingsChange,
  onResetSettings,
}: StaffGridControlsProps) {
  const [sidebarOpen, { toggle: toggleSidebar, close: closeSidebar }] =
    useDisclosure(false);

  return (
    <>
      <Stack gap="xs" pos="absolute" top={16} right={16}>
        <ColorSchemeButton {...staffGridButtonProps} />

        <StaffGridSettings
          settings={settings}
          onSettingsChange={onSettingsChange}
          onResetSettings={onResetSettings}
        />

        <ActionIcon {...staffGridButtonProps} onClick={toggleSidebar}>
          <IconMenu2 />
        </ActionIcon>

        <ActionIcon
          {...staffGridButtonProps}
          onClick={() => patternsHandlers.back()}
          disabled={patternsHistory.current === 0}
        >
          <IconArrowBackUp />
        </ActionIcon>

        <ActionIcon
          {...staffGridButtonProps}
          onClick={() => patternsHandlers.forward()}
          disabled={
            patternsHistory.current === patternsHistory.history.length - 1
          }
        >
          <IconArrowForwardUp />
        </ActionIcon>

        <ActionIcon
          {...staffGridButtonProps}
          onClick={() => patternsHandlers.set([])}
          disabled={patterns.length === 0}
        >
          <IconTrash />
        </ActionIcon>
      </Stack>

      <StaffGridSidebar
        patterns={patterns}
        onPatternsChange={patternsHandlers.set}
        opened={sidebarOpen}
        onClose={closeSidebar}
      />
    </>
  );
}
