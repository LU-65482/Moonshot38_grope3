using CommunityToolkit.Mvvm.ComponentModel;
using RunSightConfigureClient.Models;

namespace RunSightConfigureClient.ViewModels;

public partial class PairNewDeviceViewModel : ObservableObject
{
    [ObservableProperty] private DeviceConnectionInfo _connectionInfo = new();

}