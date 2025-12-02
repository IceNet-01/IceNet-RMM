package main

import (
	"fmt"
	"os"

	"github.com/icenet-rmm/agent/internal/agent"
	"github.com/spf13/cobra"
	"go.uber.org/zap"
)

var (
	version   = "0.1.0"
	buildTime = "unknown"
	gitCommit = "unknown"
)

func main() {
	// Initialize logger
	logger, _ := zap.NewProduction()
	defer logger.Sync()

	rootCmd := &cobra.Command{
		Use:   "icenet-agent",
		Short: "IceNet RMM Agent",
		Long:  `Cross-platform agent for IceNet Remote Monitoring and Management`,
	}

	// Install command
	installCmd := &cobra.Command{
		Use:   "install",
		Short: "Install and register the agent",
		RunE: func(cmd *cobra.Command, args []string) error {
			serverURL, _ := cmd.Flags().GetString("server")
			token, _ := cmd.Flags().GetString("token")

			logger.Info("Installing IceNet RMM agent",
				zap.String("server", serverURL),
				zap.String("version", version))

			installer := agent.NewInstaller(serverURL, token, logger)
			return installer.Install()
		},
	}
	installCmd.Flags().String("server", "", "RMM server URL (required)")
	installCmd.Flags().String("token", "", "Registration token (required)")
	installCmd.MarkFlagRequired("server")
	installCmd.MarkFlagRequired("token")

	// Uninstall command
	uninstallCmd := &cobra.Command{
		Use:   "uninstall",
		Short: "Uninstall the agent",
		RunE: func(cmd *cobra.Command, args []string) error {
			logger.Info("Uninstalling IceNet RMM agent")
			installer := agent.NewInstaller("", "", logger)
			return installer.Uninstall()
		},
	}

	// Run command (service mode)
	runCmd := &cobra.Command{
		Use:   "run",
		Short: "Run the agent in service mode",
		RunE: func(cmd *cobra.Command, args []string) error {
			logger.Info("Starting IceNet RMM agent",
				zap.String("version", version),
				zap.String("build", buildTime))

			agentInstance := agent.NewAgent(logger)
			return agentInstance.Run()
		},
	}

	// Version command
	versionCmd := &cobra.Command{
		Use:   "version",
		Short: "Print version information",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Printf("IceNet RMM Agent\n")
			fmt.Printf("Version: %s\n", version)
			fmt.Printf("Build Time: %s\n", buildTime)
			fmt.Printf("Git Commit: %s\n", gitCommit)
		},
	}

	// Status command
	statusCmd := &cobra.Command{
		Use:   "status",
		Short: "Check agent status",
		RunE: func(cmd *cobra.Command, args []string) error {
			logger.Info("Checking agent status")
			// TODO: Implement status check
			fmt.Println("Agent status: Running")
			return nil
		},
	}

	rootCmd.AddCommand(installCmd, uninstallCmd, runCmd, versionCmd, statusCmd)

	if err := rootCmd.Execute(); err != nil {
		logger.Error("Command failed", zap.Error(err))
		os.Exit(1)
	}
}
