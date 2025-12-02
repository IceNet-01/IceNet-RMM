package monitor

import (
	"runtime"

	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/host"
	"github.com/shirou/gopsutil/v3/mem"
	"github.com/shirou/gopsutil/v3/net"
	"go.uber.org/zap"
)

// Metrics represents system metrics
type Metrics struct {
	CPUPercent    float64 `json:"cpu_percent"`
	RAMUsed       uint64  `json:"ram_used"`
	RAMTotal      uint64  `json:"ram_total"`
	RAMPercent    float64 `json:"ram_percent"`
	DiskUsed      uint64  `json:"disk_used"`
	DiskTotal     uint64  `json:"disk_total"`
	DiskPercent   float64 `json:"disk_percent"`
	NetBytesSent  uint64  `json:"net_bytes_sent"`
	NetBytesRecv  uint64  `json:"net_bytes_recv"`
	ProcessCount  int     `json:"process_count"`
}

// Monitor handles system monitoring
type Monitor struct {
	logger *zap.Logger
}

// NewMonitor creates a new monitor instance
func NewMonitor(logger *zap.Logger) *Monitor {
	return &Monitor{logger: logger}
}

// CollectMetrics collects current system metrics
func (m *Monitor) CollectMetrics() (*Metrics, error) {
	metrics := &Metrics{}

	// CPU usage
	cpuPercents, err := cpu.Percent(0, false)
	if err == nil && len(cpuPercents) > 0 {
		metrics.CPUPercent = cpuPercents[0]
	}

	// Memory usage
	vmStat, err := mem.VirtualMemory()
	if err == nil {
		metrics.RAMUsed = vmStat.Used
		metrics.RAMTotal = vmStat.Total
		metrics.RAMPercent = vmStat.UsedPercent
	}

	// Disk usage (root/C: drive)
	diskPath := "/"
	if runtime.GOOS == "windows" {
		diskPath = "C:"
	}
	diskStat, err := disk.Usage(diskPath)
	if err == nil {
		metrics.DiskUsed = diskStat.Used
		metrics.DiskTotal = diskStat.Total
		metrics.DiskPercent = diskStat.UsedPercent
	}

	// Network I/O
	netIO, err := net.IOCounters(false)
	if err == nil && len(netIO) > 0 {
		metrics.NetBytesSent = netIO[0].BytesSent
		metrics.NetBytesRecv = netIO[0].BytesRecv
	}

	// Process count
	procs, err := host.Processes()
	if err == nil {
		metrics.ProcessCount = len(procs)
	}

	m.logger.Debug("Metrics collected",
		zap.Float64("cpu", metrics.CPUPercent),
		zap.Float64("ram", metrics.RAMPercent),
		zap.Float64("disk", metrics.DiskPercent))

	return metrics, nil
}

// GetSystemInfo returns static system information
func (m *Monitor) GetSystemInfo() map[string]interface{} {
	info := make(map[string]interface{})

	// Host info
	if hostInfo, err := host.Info(); err == nil {
		info["hostname"] = hostInfo.Hostname
		info["os"] = hostInfo.OS
		info["platform"] = hostInfo.Platform
		info["platform_version"] = hostInfo.PlatformVersion
		info["kernel_version"] = hostInfo.KernelVersion
		info["uptime"] = hostInfo.Uptime
	}

	// CPU info
	if cpuInfo, err := cpu.Info(); err == nil && len(cpuInfo) > 0 {
		info["cpu_model"] = cpuInfo[0].ModelName
		info["cpu_cores"] = cpuInfo[0].Cores
	}

	// Memory info
	if vmStat, err := mem.VirtualMemory(); err == nil {
		info["total_ram"] = vmStat.Total
	}

	// Disk info
	diskPath := "/"
	if runtime.GOOS == "windows" {
		diskPath = "C:"
	}
	if diskStat, err := disk.Usage(diskPath); err == nil {
		info["total_disk"] = diskStat.Total
	}

	info["os_type"] = runtime.GOOS
	info["arch"] = runtime.GOARCH

	return info
}
