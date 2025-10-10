use owo_colors::OwoColorize;
use similar::{ChangeTag, TextDiff};
use std::{
    env,
    fs,
    io::{self, Write},
};

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("{} verify-diff <expected> <actual>", "Usage:".bold());
        std::process::exit(1);
    }

    let expected_path = &args[1];
    let actual_path = &args[2];

    let expected = fs::read_to_string(expected_path).unwrap_or_default();
    let actual = fs::read_to_string(actual_path).unwrap_or_default();

    // Header
    println!(
        "\n{} {}\n{}: {}\n{}: {}\n",
        "📸 Snapshot Diff".bold().cyan(),
        "(Diff view)".dimmed(),
        "Expected".bold().yellow(),
        expected_path,
        "Actual".bold().yellow(),
        actual_path
    );

    // Diff computation
    let diff = TextDiff::from_lines(&expected, &actual);

    // Render with style
    for (idx, group) in diff.grouped_ops(3).iter().enumerate() {
        if idx > 0 {
            println!("{}", "───────────────────────────────────────────────".dimmed());
        }

        for op in group {
            for change in diff.iter_changes(op) {
                match change.tag() {
                    ChangeTag::Delete => print!(
                        "{} {}",
                        "-".bright_red(),
                        change.value().bright_red()
                    ),
                    ChangeTag::Insert => print!(
                        "{} {}",
                        "+".bright_green(),
                        change.value().bright_green()
                    ),
                    ChangeTag::Equal => print!("  {}", change.value().dimmed()),
                }
            }
        }
    }

    println!("\n{}", "───────────────────────────────────────────────".dimmed());

    // Prompt
    print!("{}", "\n🟢 Accept changes and replace expected? [y/N]: ".bold().cyan());
    io::stdout().flush().unwrap();

    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();

    if input.trim().eq_ignore_ascii_case("y") {
        println!("{}", "✅ Accepted".bright_green());
        std::process::exit(0);
    } else {
        println!("{}", "❌ Rejected".bright_red());
        std::process::exit(1);
    }
}
