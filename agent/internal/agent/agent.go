package agent

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/icenet-rmm/agent/internal/communication"
	"github.com/icenet-rmm/agent/internal/monitor"
	"github.com/icenet-rmm/agent/internal/update"
	"github.com/icenet-rmm/agent/pkg/config"
	"go.uber.org/zap"
)

// Agent represents the main agent instance
type Agent struct {
	config       *config.Config
	logger       *zap.Logger
	communicator *communication.Communicator
	monitor      *monitor.Monitor
	updater      *update.Updater
	ctx          context.Context
	cancel       context.CancelFunc
}

// NewAgent creates a new agent instance
func NewAgent(logger *zap.Logger) *Agent {
	ctx, cancel := context.WithCancel(context.Background())

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		logger.Fatal("Failed to load configuration", zap.Error(err))
	}

	return &Agent{
		config: cfg,
		logger: logger,
		ctx:    ctx,
		cancel: cancel,
	}
}

// Run starts the agent main loop
func (a *Agent) Run() error {
	a.logger.Info("IceNet RMM Agent starting",
		zap.String("version", a.config.Version),
		zap.String("server", a.config.ServerURL))

	// Initialize components
	if err := a.initialize(); err != nil {
		return fmt.Errorf("initialization failed: %w", err)
	}

	// Start background tasks
	go a.heartbeat()
	go a.collectMetrics()
	go a.checkForUpdates()

	// Handle shutdown signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	<-sigChan
	a.logger.Info("Shutdown signal received, gracefully shutting down...")
	a.Shutdown()

	return nil
}

// initialize sets up agent components
func (a *Agent) initialize() error {
	a.logger.Info("Initializing agent components")

	// Initialize NATS communicator
	var err error
	a.communicator, err = communication.NewCommunicator(
		a.config.ServerURL,
		a.config.AgentID,
		a.logger,
	)
	if err != nil {
		return fmt.Errorf("failed to initialize communicator: %w", err)
	}

	// Initialize system monitor
	a.monitor = monitor.NewMonitor(a.logger)

	// Initialize updater
	a.updater = update.NewUpdater(a.config, a.logger)

	a.logger.Info("Agent components initialized successfully")
	return nil
}

// heartbeat sends periodic heartbeats to server
func (a *Agent) heartbeat() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-a.ctx.Done():
			return
		case <-ticker.C:
			if err := a.communicator.SendHeartbeat(); err != nil {
				a.logger.Error("Failed to send heartbeat", zap.Error(err))
			}
		}
	}
}

// collectMetrics collects and sends system metrics
func (a *Agent) collectMetrics() {
	ticker := time.NewTicker(5 * time.Minute)
	defer ticker.Stop()

	for {
		select {
		case <-a.ctx.Done():
			return
		case <-ticker.C:
			metrics, err := a.monitor.CollectMetrics()
			if err != nil {
				a.logger.Error("Failed to collect metrics", zap.Error(err))
				continue
			}

			if err := a.communicator.SendMetrics(metrics); err != nil {
				a.logger.Error("Failed to send metrics", zap.Error(err))
			}
		}
	}
}

// checkForUpdates checks for agent and software updates
func (a *Agent) checkForUpdates() {
	ticker := time.NewTicker(1 * time.Hour)
	defer ticker.Stop()

	for {
		select {
		case <-a.ctx.Done():
			return
		case <-ticker.C:
			if err := a.updater.CheckForUpdates(); err != nil {
				a.logger.Error("Failed to check for updates", zap.Error(err))
			}
		}
	}
}

// Shutdown gracefully shuts down the agent
func (a *Agent) Shutdown() {
	a.logger.Info("Shutting down agent")
	a.cancel()

	if a.communicator != nil {
		a.communicator.Close()
	}

	a.logger.Info("Agent shutdown complete")
}
