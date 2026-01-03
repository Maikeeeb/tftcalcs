import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Accordion, AccordionDetails, AccordionSummary, Box, Stack, Typography } from '@mui/material';
import { ObjectFieldTemplateProps, getDefaultRegistry } from '@rjsf/utils';
import { useMemo } from 'react';

const advancedFieldNames = new Set([
  'json_path',
  'set_id',
  'metatft_txt_path',
  'beam_width',
  'blacklist_traits_by_name',
]);

const RootObjectFieldTemplate = (props: ObjectFieldTemplateProps) => {
  const registry = useMemo(() => props.registry ?? getDefaultRegistry(), [props.registry]);
  const DefaultObjectFieldTemplate = registry.templates.ObjectFieldTemplate;

  if (props.idSchema.$id !== 'root') {
    return <DefaultObjectFieldTemplate {...props} />;
  }

  const DescriptionFieldTemplate = registry.templates.DescriptionFieldTemplate;
  const regularFields = props.properties.filter((prop) => !advancedFieldNames.has(prop.name));
  const advancedFields = props.properties.filter((prop) => advancedFieldNames.has(prop.name));

  return (
    <Stack spacing={2}>
      {props.title ? (
        <Typography variant="h6" component="h2">
          {props.title}
        </Typography>
      ) : null}

      {props.description ? (
        <DescriptionFieldTemplate
          id={`${props.idSchema.$id}__description`}
          description={props.description}
          schema={props.schema}
          uiSchema={props.uiSchema}
          registry={registry}
        />
      ) : null}

      <Stack spacing={2}>
        {regularFields.map((prop) => (
          <Box key={prop.name}>{prop.content}</Box>
        ))}
      </Stack>

      {advancedFields.length ? (
        <Accordion disableGutters>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box>
              <Typography variant="subtitle1">Advanced solver settings</Typography>
              <Typography variant="body2" color="text.secondary">
                JSON path, set id, MetaTFT export path, beam width, and trait blacklist.
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Stack spacing={2}>
              {advancedFields.map((prop) => (
                <Box key={prop.name}>{prop.content}</Box>
              ))}
            </Stack>
          </AccordionDetails>
        </Accordion>
      ) : null}
    </Stack>
  );
};

export default RootObjectFieldTemplate;
