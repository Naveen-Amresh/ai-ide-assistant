package bench;

import java.sql.Array;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.ConnectionCallback;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
public class BenchApplication {

    public static void main(String[] args) {
        SpringApplication.run(BenchApplication.class, args);
    }

    record Message(String message) {}

    record Item(int id, String name, double price, int quantity, List<String> tags, OffsetDateTime createdAt) {}

    record ItemIn(
            @NotBlank @Size(max = 100) String name,
            @Positive double price,
            @PositiveOrZero int quantity,
            @NotNull List<String> tags) {
        ItemIn {
            if (tags == null) tags = List.of();
        }
    }

    @RestController
    static class Api {
        static final int ROWS = 10_000;
        static final String COLS = "id, name, price, quantity, tags, created_at";
        static final String SQL_ONE = "SELECT " + COLS + " FROM items WHERE id = ?";
        static final String SQL_MANY = "SELECT " + COLS + " FROM items ORDER BY id LIMIT ?";
        static final String SQL_INSERT =
                "INSERT INTO items (name, price, quantity, tags) VALUES (?, ?, ?, ?) RETURNING " + COLS;
        static final Message HELLO = new Message("Hello, World!");

        static final RowMapper<Item> ROW = (rs, n) -> toItem(rs);

        private final JdbcTemplate jdbc;

        Api(JdbcTemplate jdbc) {
            this.jdbc = jdbc;
        }

        static Item toItem(ResultSet rs) throws SQLException {
            Array tags = rs.getArray(5);
            return new Item(rs.getInt(1), rs.getString(2), rs.getDouble(3), rs.getInt(4),
                    List.of((String[]) tags.getArray()), rs.getObject(6, OffsetDateTime.class));
        }

        static int randomId() {
            return ThreadLocalRandom.current().nextInt(1, ROWS + 1);
        }

        static int clamp(int n) {
            return Math.max(1, Math.min(500, n));
        }

        @GetMapping("/json")
        Message json() {
            return HELLO;
        }

        @GetMapping("/db")
        Item db() {
            return jdbc.queryForObject(SQL_ONE, ROW, randomId());
        }

        // One connection, one prepared statement, n round-trips (same as the asyncpg apps).
        @GetMapping("/queries")
        List<Item> queries(@RequestParam(defaultValue = "20") int n) {
            int count = clamp(n);
            return jdbc.execute((ConnectionCallback<List<Item>>) conn -> {
                List<Item> out = new ArrayList<>(count);
                try (PreparedStatement ps = conn.prepareStatement(SQL_ONE)) {
                    for (int i = 0; i < count; i++) {
                        ps.setInt(1, randomId());
                        try (ResultSet rs = ps.executeQuery()) {
                            rs.next();
                            out.add(toItem(rs));
                        }
                    }
                }
                return out;
            });
        }

        @GetMapping("/items")
        List<Item> items(@RequestParam(defaultValue = "100") int limit) {
            return jdbc.query(SQL_MANY, ROW, clamp(limit));
        }

        @PostMapping("/items")
        @ResponseStatus(HttpStatus.CREATED)
        Item create(@Valid @RequestBody ItemIn in) {
            return jdbc.execute((ConnectionCallback<Item>) conn -> {
                try (PreparedStatement ps = conn.prepareStatement(SQL_INSERT)) {
                    ps.setString(1, in.name());
                    ps.setDouble(2, in.price());
                    ps.setInt(3, in.quantity());
                    ps.setArray(4, conn.createArrayOf("text", in.tags().toArray()));
                    try (ResultSet rs = ps.executeQuery()) {
                        rs.next();
                        return toItem(rs);
                    }
                }
            });
        }
    }
}
