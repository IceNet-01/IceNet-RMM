package agent

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"

	"go.uber.org/zap"
)

// Installer handles agent installation and registration
type Installer struct {
	serverURL string
	token     string
	logger    *zap.Logger
}

// NewInstaller creates a new installer instance
func NewInstaller(serverURL, token string, logger *zap.Logger) *Installer {
	return &Installer{
		serverURL: serverURL,
		token:     token,
		logger:    logger,
	}
}

// Install installs and registers the agent
func (i *Installer) Install() error {
	i.logger.Info("Starting installation",
		zap.String("os", runtime.GOOS),
		zap.String("arch", runtime.GOARCH))

	// Create installation directory
	installDir := i.getInstallDir()
	if err := os.MkdirAll(installDir, 0755); err != nil {
		return fmt.Errorf("failed to create install directory: %w", err)
	}

	// Copy agent binary
	if err := i.copyBinary(installDir); err != nil {
		return fmt.Errorf("failed to copy binary: %w", err)
	}

	// Create configuration
	if err := i.createConfig(installDir); err != nil {
		return fmt.Errorf("failed to create config: %w", err)
	}

	// Register with server
	if err := i.registerAgent(); err != nil {
		return fmt.Errorf("failed to register agent: %w", err)
	}

	// Install as service
	if err := i.installService(); err != nil {
		return fmt.Errorf("failed to install service: %w", err)
	}

	i.logger.Info("Installation completed successfully")
	return nil
}

// Uninstall removes the agent
func (i *Installer) Uninstall() error {
	i.logger.Info("Starting uninstallation")

	// Stop and remove service
	if err := i.uninstallService(); err != nil {
		i.logger.Error("Failed to uninstall service", zap.Error(err))
	}

	// Remove installation directory
	installDir := i.getInstallDir()
	if err := os.RemoveAll(installDir); err != nil {
		return fmt.Errorf("failed to remove install directory: %w", err)
	}

	i.logger.Info("Uninstallation completed successfully")
	return nil
}

// getInstallDir returns the installation directory based on OS
func (i *Installer) getInstallDir() string {
	switch runtime.GOOS {
	case "windows":
		return filepath.Join(os.Getenv("ProgramFiles"), "IceNet", "Agent")
	case "linux", "darwin":
		return "/opt/icenet/agent"
	default:
		return "/opt/icenet/agent"
	}
}

// copyBinary copies the agent binary to installation directory
func (i *Installer) copyBinary(installDir string) error {
	// Get current executable path
	exePath, err := os.Executable()
	if err != nil {
		return err
	}

	// Destination path
	destPath := filepath.Join(installDir, filepath.Base(exePath))

	// Copy file
	input, err := os.ReadFile(exePath)
	if err != nil {
		return err
	}

	if err := os.WriteFile(destPath, input, 0755); err != nil {
		return err
	}

	i.logger.Info("Binary copied", zap.String("destination", destPath))
	return nil
}

// createConfig creates the agent configuration file
func (i *Installer) createConfig(installDir string) error {
	configPath := filepath.Join(installDir, "config.yaml")

	config := fmt.Sprintf(`
server_url: %s
registration_token: %s
check_in_interval: 30
log_level: info
`, i.serverURL, i.token)

	if err := os.WriteFile(configPath, []byte(config), 0644); err != nil {
		return err
	}

	i.logger.Info("Configuration created", zap.String("path", configPath))
	return nil
}

// registerAgent registers the agent with the server
func (i *Installer) registerAgent() error {
	// TODO: Implement server registration via HTTP API
	i.logger.Info("Registering agent with server", zap.String("server", i.serverURL))
	// This will make an HTTP POST to /api/agents/register with system info
	return nil
}

// installService installs the agent as a system service
func (i *Installer) installService() error {
	switch runtime.GOOS {
	case "windows":
		return i.installWindowsService()
	case "linux":
		return i.installLinuxService()
	default:
		return fmt.Errorf("service installation not supported on %s", runtime.GOOS)
	}
}

// uninstallService removes the agent service
func (i *Installer) uninstallService() error {
	switch runtime.GOOS {
	case "windows":
		return i.uninstallWindowsService()
	case "linux":
		return i.uninstallLinuxService()
	default:
		return fmt.Errorf("service uninstallation not supported on %s", runtime.GOOS)
	}
}

// installWindowsService installs the agent as a Windows service
func (i *Installer) installWindowsService() error {
	i.logger.Info("Installing Windows service")
	// TODO: Implement Windows service installation using golang.org/x/sys/windows/svc
	return nil
}

// uninstallWindowsService removes the Windows service
func (i *Installer) uninstallWindowsService() error {
	i.logger.Info("Uninstalling Windows service")
	// TODO: Implement Windows service uninstallation
	return nil
}

// installLinuxService installs the agent as a systemd service
func (i *Installer) installLinuxService() error {
	i.logger.Info("Installing systemd service")

	serviceContent := `[Unit]
Description=IceNet RMM Agent
After=network.target

[Service]
Type=simple
ExecStart=/opt/icenet/agent/icenet-agent run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
`

	if err := os.WriteFile("/etc/systemd/system/icenet-agent.service", []byte(serviceContent), 0644); err != nil {
		return err
	}

	// TODO: Execute systemctl commands to enable and start service
	return nil
}

// uninstallLinuxService removes the systemd service
func (i *Installer) uninstallLinuxService() error {
	i.logger.Info("Uninstalling systemd service")

	// TODO: Execute systemctl commands to stop and disable service
	os.Remove("/etc/systemd/system/icenet-agent.service")
	return nil
}
