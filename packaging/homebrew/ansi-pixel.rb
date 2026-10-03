# Homebrew Formula for ansi-pixel
# To publish in a custom tap:
# 1. Create a repository named `homebrew-tap` under your GitHub account (e.g. `github.com/senurah/homebrew-tap`).
# 2. Place this file at `Formula/ansi-pixel.rb` in that repository.
# 3. Users can then install via:
#      brew tap senurah/tap
#      brew install ansi-pixel

class AnsiPixel < Formula
  desc "Convert images to truecolor ANSI pixel art directly in your terminal"
  homepage "https://github.com/senurah/ansi-pixel"
  version "0.2.0"
  license "MIT"

  on_macos do
    if Hardware::CPU.arm?
      url "https://github.com/senurah/ansi-pixel/releases/download/v#{version}/ansi-pixel-darwin-arm64"
      # sha256 "REPLACE_WITH_DARWIN_ARM64_SHA256"

      def install
        bin.install "ansi-pixel-darwin-arm64" => "ansi-pixel"
      end
    else
      url "https://github.com/senurah/ansi-pixel/releases/download/v#{version}/ansi-pixel-darwin-x86_64"
      # sha256 "REPLACE_WITH_DARWIN_X86_64_SHA256"

      def install
        bin.install "ansi-pixel-darwin-x86_64" => "ansi-pixel"
      end
    end
  end

  on_linux do
    if Hardware::CPU.intel?
      url "https://github.com/senurah/ansi-pixel/releases/download/v#{version}/ansi-pixel-linux-x86_64"
      # sha256 "REPLACE_WITH_LINUX_X86_64_SHA256"

      def install
        bin.install "ansi-pixel-linux-x86_64" => "ansi-pixel"
      end
    end
  end

  test do
    assert_match "Convert images to truecolor ANSI pixel art", shell_output("#{bin}/ansi-pixel --help")
    assert_match "ansi-pixel #{version}", shell_output("#{bin}/ansi-pixel --version")
  end
end
