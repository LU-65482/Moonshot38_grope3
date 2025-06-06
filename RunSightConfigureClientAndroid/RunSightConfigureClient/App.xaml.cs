﻿using Microsoft.Extensions.Hosting;
using RunSightConfigureClient.Services;

namespace RunSightConfigureClient;

public partial class App : Application
{
    public static IHost? Host { get; private set; }

    public static T GetService<T>() where T : class
    {
        var s = Host?.Services.GetRequiredService<T>();
        return s ?? throw new InvalidOperationException();
    }
    
    public App()
    {
        InitializeComponent();
        SetupHost();
        MainPage = new AppShell();
    }

    public void SetupHost()
    {
        Host = Microsoft.Extensions.Hosting.Host.CreateDefaultBuilder()
            .ConfigureServices((context, services) =>
            {
                services.AddSingleton<DeviceConnectionService>();
            })
            .Build();
    }
}