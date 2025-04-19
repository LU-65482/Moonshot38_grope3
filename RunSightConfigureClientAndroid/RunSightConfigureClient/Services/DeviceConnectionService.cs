using System.Text.Json;
using Grpc.Core;
using Microsoft.Extensions.Logging;
using RunSightConfigureClient.Models;

namespace RunSightConfigureClient.Services;

public class DeviceConnectionService(ILogger<DeviceConnectionService> logger)
{
    public ILogger<DeviceConnectionService> Logger { get; } = logger;
    
    public DeviceConnectionInfo? CurrentConnectedDevice { get; private set; }

    public DeviceConfigure CurrentDeviceConfigure { get; set; } = new();

    public Uri? BaseUrl { get; private set; } 
    
    public async Task ConnectToNewDevice(DeviceConnectionInfo info)
    {
        try
        {
            var uri = new UriBuilder()
            {
                Host = info.DeviceAddress,
                Port = info.DevicePort,
                Scheme = "http"
            }.Uri;
            BaseUrl = uri;
            var httpClient = new HttpClient();
            var json = await httpClient.GetAsync(new UriBuilder(uri)
            {
                Path = "configure"
            }.Uri);
            CurrentDeviceConfigure = JsonSerializer.Deserialize<DeviceConfigure>(await json.Content.ReadAsStringAsync())!;
        }
        catch (Exception e)
        {
            Logger.LogError(e, "无法连接到设备");
            throw;
        }
    }

    private void DisconnectFromCurrentDevice()
    {
        CurrentConnectedDevice = null;
    }
}