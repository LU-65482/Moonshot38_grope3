using CommunityToolkit.Mvvm.ComponentModel;

namespace RunSightConfigureClient.Models;

public partial class DeviceConnectionInfo : ObservableObject
{
    [ObservableProperty] private string _deviceAddress = "";
    
    [ObservableProperty] private int _devicePort = 20721;
}