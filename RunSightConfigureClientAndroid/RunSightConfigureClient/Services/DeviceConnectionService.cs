using Grpc.Core;
using Microsoft.Extensions.Logging;
using RunSightConfigureClient.Models;

namespace RunSightConfigureClient.Services;

public class DeviceConnectionService(ILogger<DeviceConnectionService> logger)
{
    public ILogger<DeviceConnectionService> Logger { get; } = logger;
    
    public Channel? CurrentGrpcChannel { get; private set; }
    
    public DeviceConnectionInfo? CurrentConnectedDevice { get; private set; }

    public void ConnectToNewDevice(DeviceConnectionInfo info)
    {
        if (CurrentConnectedDevice != null)
        {
            DisconnectFromCurrentDevice();
        }

        CurrentConnectedDevice = info;
        
        try
        {
            CurrentGrpcChannel = new Channel(info.DeviceAddress, info.DevicePort, ChannelCredentials.Insecure);
            CurrentGrpcChannel.ConnectAsync().Wait();
            Logger.LogInformation($"Connected to device at {info.DeviceAddress}:{info.DevicePort}");
        }
        catch (Exception ex)
        {
            Logger.LogError(ex, "Failed to connect to device");
            throw;
        }
    }

    private void DisconnectFromCurrentDevice()
    {
        if (CurrentGrpcChannel != null)
        {
            try
            {
                CurrentGrpcChannel.ShutdownAsync().Wait();
                Logger.LogInformation($"Disconnected from device at {CurrentConnectedDevice.DeviceAddress}:{CurrentConnectedDevice.DevicePort}");
            }
            catch (Exception ex)
            {
                Logger.LogError(ex, "Failed to disconnect from device");
            }
        }

        CurrentConnectedDevice = null;
    }
}