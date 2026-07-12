# infrastructure/audio_manager.py

from __future__ import annotations

from pathlib import Path

import pygame


class AudioManager:
    """
    Safe application sound-effect manager.

    Audio failure never prevents the game from running. Missing files,
    unsupported codecs, and unavailable audio devices are reported once
    through the console and otherwise ignored.
    """

    SOUND_FILES = {
        "disc_drop": "disc_drop.mp3",
        "win": "win.mp3",
        "button_click": "button_click.mp3",
    }

    def __init__(
        self,
        *,
        enabled: bool = True,
        master_volume: float = 0.70,
        audio_directory: Path | str | None = None,
    ) -> None:
        self.enabled = bool(enabled)
        self.master_volume = self._clamp_volume(
            master_volume
        )

        self.available = False
        self.sounds: dict[
            str,
            pygame.mixer.Sound,
        ] = {}

        if audio_directory is None:
            project_root = (
                Path(__file__)
                .resolve()
                .parents[1]
            )

            audio_directory = (
                project_root
                / "assets"
                / "audio"
            )

        self.audio_directory = Path(
            audio_directory
        )

        self._initialize_mixer()
        self._load_sounds()
        self._apply_volume()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def _initialize_mixer(self) -> None:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()

        except pygame.error as error:
            print(
                "[Audio] Audio device unavailable. "
                f"Sound is disabled: {error}"
            )
            return

        self.available = True

    def _load_sounds(self) -> None:
        if not self.available:
            return

        for name, filename in (
            self.SOUND_FILES.items()
        ):
            path = (
                self.audio_directory
                / filename
            )

            if not path.is_file():
                print(
                    "[Audio] Missing sound file: "
                    f"{path}"
                )
                continue

            try:
                self.sounds[name] = (
                    pygame.mixer.Sound(
                        str(path)
                    )
                )

            except (
                pygame.error,
                OSError,
            ) as error:
                print(
                    "[Audio] Could not load "
                    f"{path.name}: {error}"
                )

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def apply_config(
        self,
        *,
        enabled: bool,
        master_volume: float,
    ) -> None:
        self.enabled = bool(enabled)

        self.master_volume = (
            self._clamp_volume(
                master_volume
            )
        )

        self._apply_volume()

    def set_enabled(
        self,
        enabled: bool,
    ) -> None:
        self.enabled = bool(enabled)

    def set_master_volume(
        self,
        volume: float,
    ) -> None:
        self.master_volume = (
            self._clamp_volume(volume)
        )

        self._apply_volume()

    def _apply_volume(self) -> None:
        for sound in self.sounds.values():
            sound.set_volume(
                self.master_volume
            )

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def play(
        self,
        name: str,
    ) -> None:
        if not self.available:
            return

        if not self.enabled:
            return

        if self.master_volume <= 0.0:
            return

        sound = self.sounds.get(name)

        if sound is None:
            return

        try:
            sound.play()
        except pygame.error:
            pass

    def play_disc_drop(self) -> None:
        self.play("disc_drop")

    def play_win(self) -> None:
        self.play("win")

    def play_button_click(self) -> None:
        self.play("button_click")

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        if not self.available:
            return

        try:
            pygame.mixer.stop()
        except pygame.error:
            pass

        self.sounds.clear()

    @staticmethod
    def _clamp_volume(
        value: float,
    ) -> float:
        try:
            volume = float(value)
        except (TypeError, ValueError):
            volume = 0.70

        return max(
            0.0,
            min(volume, 1.0),
        )
