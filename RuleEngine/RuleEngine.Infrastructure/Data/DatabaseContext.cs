using Microsoft.Data.SqlClient;
using Microsoft.Extensions.Options;
using RuleEngine.Infrastructure.Configuration;

namespace RuleEngine.Infrastructure.Data;

public class DatabaseContext
{
    private readonly DatabaseSettings _settings;

    public DatabaseContext(IOptions<DatabaseSettings> settings)
    {
        _settings = settings.Value;
    }

    public SqlConnection CreateConnection()
    {
        return new SqlConnection(_settings.ConnectionString);
    }
}
