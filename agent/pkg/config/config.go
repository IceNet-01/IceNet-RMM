package config

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"

	"github.com/spf13/viper"
)

// Config holds agent configuration
type Config struct {
	ServerURL         string `mapstructure:"server_url"`
	AgentID           string `mapstructure:"agent_id"`
	RegistrationToken string `mapstructure:"registration_token"`
	CheckInInterval   int    `mapstructure:"check_in_interval"`
	LogLevel          string `mapstructure:"log_level"`
	Version           string
}

// Load loads configuration from file
func Load() (*Config, error) {
	configPath := getConfigPath()

	viper.SetConfigFile(configPath)
	viper.SetConfigType("yaml")

	// Set defaults
	viper.SetDefault("check_in_interval", 30)
	viper.SetDefault("log_level", "info")

	if err := viper.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("failed to read config: %w", err)
	}

	var config Config
	if err := viper.Unmarshal(&config); err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %w", err)
	}

	config.Version = "0.1.0"

	return &config, nil
}

// getConfigPath returns the config file path based on OS
func getConfigPath() string {
	switch runtime.GOOS {
	case "windows":
		return filepath.Join(os.Getenv("ProgramFiles"), "IceNet", "Agent", "config.yaml")
	case "linux", "darwin":
		return "/opt/icenet/agent/config.yaml"
	default:
		return "./config.yaml"
	}
}
