using RuleEngine.Application.Interfaces;
using RuleEngine.Infrastructure.Configuration;
using RuleEngine.Infrastructure.Data;
using RuleEngine.Infrastructure.Repositories;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new() { Title = "Rule Engine API", Version = "v1", Description = "Awards and Rules Management API for RosteredAI" });
});

// Configure Database Settings
builder.Services.Configure<DatabaseSettings>(
    builder.Configuration.GetSection("DatabaseSettings"));

// Register services
builder.Services.AddSingleton<DatabaseContext>();
builder.Services.AddScoped<IRuleEngineRepository, RuleEngineRepository>();

// Register MediatR
builder.Services.AddMediatR(cfg => {
    cfg.RegisterServicesFromAssembly(typeof(RuleEngine.Application.Commands.CompileAwardsSummary.CompileAwardsSummaryCommand).Assembly);
});

// Add CORS
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();

// Configure the HTTP request pipeline (enable Swagger in all environments for ops)
app.UseSwagger(c =>
{
    // Serve swagger.json at /ruleapi/swagger/v1/swagger.json so it's accessible through nginx /ruleapi block
    c.RouteTemplate = "ruleapi/swagger/{documentName}/swagger.json";
});

app.UseSwaggerUI(c =>
{
    // Point to the swagger.json at the absolute path through nginx reverse proxy
    c.SwaggerEndpoint("/ruleapi/swagger/v1/swagger.json", "Rule Engine API v1");
    c.RoutePrefix = "ruleapi/swagger";
});

// app.UseHttpsRedirection(); // Disabled for local development
app.UseCors("AllowAll");
app.UseAuthorization();
app.MapControllers();

app.Run();
