using System.Net.Http.Headers;
using System.Net.Http.Json;
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

    public void DisconnectFromCurrentDevice()
    {
        CurrentConnectedDevice = null;
    }
    
    public async Task UploadSettings()
    {
        try
        {
            var httpClient = new HttpClient();
            var r = await httpClient.PostAsync(new UriBuilder(BaseUrl)
            {
                Path = "configure"
            }.Uri, JsonContent.Create(CurrentDeviceConfigure, new MediaTypeHeaderValue("application/json")
            {
                CharSet = "utf-8"
            }));
            Logger.LogInformation("response: {}", await r.Content.ReadAsStringAsync());
            r.EnsureSuccessStatusCode();
        }
        catch (Exception e)
        {
            Logger.LogError(e, "无法保存配置");
            throw;
        }
    }
}