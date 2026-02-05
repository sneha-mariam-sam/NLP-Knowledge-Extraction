import argparse
import os
from pathlib import Path

import pandas as pd
import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer, pipeline

### using GPU if available
device = torch.device(torch.device("cuda:0" if torch.cuda.is_available() else "cpu"))
torch.manual_seed(1000)

RELATIONS = {
    "CountryBordersWithCountry",
    "RiverBasinsCountry",
    "PersonLanguage",
    "PersonProfession",
    "PersonInstrument"
}

def initialize_lm(model_type, top_k):
    ### using the HuggingFace pipeline to initialize the model and its corresponding tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_type)
    model = AutoModelForMaskedLM.from_pretrained(model_type).to(device)
    device_id = (
        -1 if device == torch.device("cpu") else 0
    )  ### -1 device is for cpu, 0 for gpu
    nlp = pipeline(
        "fill-mask", model=model, tokenizer=tokenizer, top_k=top_k, device=device_id
    )  ### top_k defines the number of ranked output tokens to pick in the [MASK] position
    return nlp, tokenizer.mask_token

def create_prompt(subject_entity: str, relation: str, mask_token: str) -> str:
    """
    Create relation-specific prompt with [MASK] token.
    """
    relation_prompts = {
        "CountryBordersWithCountry": f"The neighbouring country of {subject_entity} is {mask_token}.",
        "RiverBasinsCountry": f"{subject_entity} river is a river basin in the country {mask_token}.",
        "PersonLanguage": f"{subject_entity} speaks in {mask_token}.",
        "PersonProfession": f"{subject_entity} is a {mask_token} by profession.",
        "PersonInstrument": f"{subject_entity} plays {mask_token}, which is an instrument."
    }

    return relation_prompts.get(relation, f"{subject_entity} relates to {mask_token}.")

# -------------------------
# Probing LM
# -------------------------
def probe_lm(model_name: str, top_k: int, relation: str, subject_entities: list, output_dir: Path):
    """
    Probe masked LM for all subject entities for a given relation.
    Save outputs with token probabilities to CSV.
    """
    nlp_pipeline, mask_token = initialize_lm(model_name, top_k)
    results = []

    for entity in subject_entities:
        print(f"Probing {model_name} for {entity} ({relation})")
        prompt = create_prompt(entity, relation, mask_token)
        outputs = nlp_pipeline(prompt)

        for out in outputs:
            results.append({
                "Prompt": prompt,
                "SubjectEntity": entity,
                "Relation": relation,
                "ObjectEntity": out["token_str"],
                "Probability": round(out["score"], 4)
            })

    # Save raw prompt outputs
    df = pd.DataFrame(results).sort_values(by=["SubjectEntity", "Probability"], ascending=[True, False])
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_dir / f"{relation}.csv", index=False)

# -------------------------
# Apply Probability Threshold
# -------------------------
def filter_by_probability(input_dir: Path, thresholds: list, relations: set, output_dir: Path):
    """
    Select predicted tokens based on probability thresholds.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    for relation in relations:
        df = pd.read_csv(input_dir / f"{relation}.csv")
        thresh = thresholds[0] if (df["Probability"] >= thresholds[0]).any() else thresholds[1]
        df_filtered = df[df["Probability"] >= thresh]
        df_filtered.to_csv(output_dir / f"{relation}.csv", index=False)

# -------------------------
# Main Solution
# -------------------------
def your_solution(input_dir: Path, prob_threshold: list, relations: set, output_dir: Path):
    """
    Filter the prompt outputs based on probability thresholds.
    """
    filter_by_probability(input_dir, prob_threshold, relations, output_dir)

# -------------------------
# CLI Entry Point
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Probe LM and generate relation outputs")
    parser.add_argument("--model_type", type=str, default="bert-base-uncased", help="HuggingFace model name")
    parser.add_argument("--input_dir", type=str, default="./dataset/test/", help="Input CSV directory")
    parser.add_argument("--prompt_output_dir", type=str, default="./prompt_output/", help="Prompt outputs directory")
    parser.add_argument("--solution_output_dir", type=str, default="./solution/", help="Filtered outputs directory")
    args = parser.parse_args()

    model_name = args.model_type
    input_dir = Path(args.input_dir)
    prompt_dir = Path(args.prompt_output_dir)
    solution_dir = Path(args.solution_output_dir)

    top_k = 200
    prob_threshold = [0.3, 0.1]

    # Probe LM for each relation
    for relation in RELATIONS:
        entities = pd.read_csv(input_dir / f"{relation}.csv")["SubjectEntity"].drop_duplicates().tolist()
        probe_lm(model_name, top_k, relation, entities, prompt_dir)

    # Filter outputs by probability threshold
    your_solution(prompt_dir, prob_threshold, RELATIONS, solution_dir)


if __name__ == "__main__":
    main()

#References:
#https://datatofish.com/if-condition-in-pandas-dataframe/
